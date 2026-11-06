# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Static tests for the coordinated OpenTelemetry security lock update."""
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "apps/api"
STABLE = {
    "opentelemetry-api",
    "opentelemetry-sdk",
    "opentelemetry-exporter-otlp",
    "opentelemetry-exporter-otlp-proto-grpc",
}
INSTRUMENTATION = {"opentelemetry-instrumentation-django"}


class OpenTelemetryLockTests(unittest.TestCase):
    def test_direct_pins_agree_with_lock(self):
        project = tomllib.loads((API / "pyproject.toml").read_text())
        lock = tomllib.loads((API / "uv.lock").read_text())
        locked = {p["name"]: p["version"] for p in lock["package"]}
        for package in STABLE | INSTRUMENTATION:
            expected = "0.66b1" if package in INSTRUMENTATION else "1.45.1"
            with self.subTest(package=package):
                self.assertIn(f"{package}=={expected}", project["project"]["dependencies"])
                self.assertEqual(locked[package], expected)

    def test_all_related_resolutions_are_coordinated(self):
        lock = tomllib.loads((API / "uv.lock").read_text())
        related = [(p["name"], p["version"]) for p in lock["package"]
                   if p["name"].startswith("opentelemetry-")]
        self.assertGreaterEqual(len(related), 12)
        for name, version in related:
            with self.subTest(package=name):
                self.assertIn(version, {"1.45.1", "0.66b1"})
        self.assertEqual(len(lock['package']), 122)


if __name__ == "__main__":
    unittest.main()
