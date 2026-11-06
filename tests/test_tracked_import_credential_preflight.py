# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Bounded, offline credential preflight for tracked public-import files.

This is a high-confidence regression guard, not a comprehensive secret scan.
It never prints discovered token values and does not contact any service.
"""
from functools import lru_cache
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAX_SCAN_BYTES = 2_000_000
EXPECTED_AWS_DOCUMENTATION_KEY = "AKIA" + "IOSFODNN7EXAMPLE"
EXPECTED_AWS_DOCUMENTATION_PATH = "apps/api/plane/api/views/issue.py"

PRIVATE_KEY_BLOCK = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")
GITHUB_TOKEN = re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}")
AWS_ACCESS_KEY_ID = re.compile(rb"\bAKIA[0-9A-Z]{16}\b")
NPMRC_LITERAL_TOKEN = re.compile(rb"(?m)^\s*(?://[^\r\n]+:)?_authToken\s*=\s*([^\s#\r\n]+)")


@lru_cache(maxsize=1)
def tracked_files():
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return tuple(
        name.decode("utf-8", errors="surrogateescape")
        for name in result.stdout.split(b"\0")
        if name
    )


@lru_cache(maxsize=1)
def bounded_text_contents():
    sources = []
    for name in tracked_files():
        path = ROOT / name
        if not path.is_file() or path.stat().st_size > MAX_SCAN_BYTES:
            continue
        payload = path.read_bytes()
        if b"\0" in payload:
            continue
        sources.append((name, payload))
    return tuple(sources)


def location(payload, offset):
    return payload[:offset].count(b"\n") + 1


class PublicImportCredentialPreflightTests(unittest.TestCase):
    def test_tracked_files_do_not_include_unexpected_sensitive_filenames(self):
        disallowed = []
        for name in tracked_files():
            path = Path(name)
            lower = path.name.lower()
            parts = {part.lower() for part in path.parts}
            if lower.startswith(".env") and lower != ".env.example":
                disallowed.append(name)
            if lower in {"id_rsa", "id_ed25519", "credentials", ".pypirc"}:
                disallowed.append(name)
            if any(part in {".ssh", ".aws"} for part in parts):
                disallowed.append(name)
            if path.suffix.lower() in {".pem", ".p12", ".pfx", ".key", ".jks", ".keystore", ".kdbx"}:
                disallowed.append(name)
        self.assertEqual(sorted(set(disallowed)), [])

    def test_no_embedded_private_key_blocks_or_github_pat_markers(self):
        findings = []
        for name, payload in bounded_text_contents():
            for marker, pattern in (
                ("private-key-block", PRIVATE_KEY_BLOCK),
                ("github-personal-access-token", GITHUB_TOKEN),
            ):
                for match in pattern.finditer(payload):
                    findings.append((name, location(payload, match.start()), marker))
        # Report source locations only, never a private key or token value.
        self.assertEqual(findings, [])

    def test_aws_style_access_keys_are_only_the_documentation_example(self):
        findings = []
        for name, payload in bounded_text_contents():
            for match in AWS_ACCESS_KEY_ID.finditer(payload):
                if (
                    name == EXPECTED_AWS_DOCUMENTATION_PATH
                    and match.group().decode("ascii") == EXPECTED_AWS_DOCUMENTATION_KEY
                ):
                    continue
                findings.append((name, location(payload, match.start())))
        self.assertEqual(findings, [])

    def test_npmrc_files_do_not_embed_literal_auth_tokens(self):
        findings = []
        for name, payload in bounded_text_contents():
            if Path(name).name != ".npmrc":
                continue
            for match in NPMRC_LITERAL_TOKEN.finditer(payload):
                # Environment variable interpolation is not a hard-coded secret.
                value = match.group(1)
                if re.fullmatch(rb"\$\{[A-Za-z_][A-Za-z0-9_]*\}", value):
                    continue
                findings.append((name, location(payload, match.start())))
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
