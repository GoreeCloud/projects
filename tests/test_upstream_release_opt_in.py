# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Isolated regression tests of the imported instance version check method.

Uses the actual method body with fake HTTP and environment modules.
No real DNS, HTTP, Django app, database or external credentials are used.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / (
    "apps/api/plane/license/management/commands/register_instance.py"
)
UPSTREAM = "https://api.github.com/repos/makeplane/plane/releases/latest"


def load_method(value, *, response_tag="v1.2.3", fail=False):
    tree = ast.parse(SOURCE.read_text())
    command = next(item for item in tree.body
                   if isinstance(item, ast.ClassDef) and item.name == "Command")
    method = next(item for item in command.body
                  if isinstance(item, ast.FunctionDef)
                  and item.name == "check_for_latest_version")
    method.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    requests_seen = []
    notices = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"tag_name": response_tag}

    def fake_get(url, *, timeout):
        requests_seen.append((url, timeout))
        if fail:
            raise ConnectionError("synthetic offline error")
        return Response()

    namespace = {
        "os": SimpleNamespace(environ=(
            {} if value is None else {"GOREECLOUD_ALLOW_UPSTREAM_RELEASE_CHECK": value}
        )),
        "requests": SimpleNamespace(get=fake_get),
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    instance = SimpleNamespace(stdout=SimpleNamespace(write=notices.append))
    return namespace["check_for_latest_version"], instance, requests_seen, notices


class UpstreamReleaseCheckTests(unittest.TestCase):
    def test_default_and_malformed_values_never_use_network(self):
        for value in (None, "", "false", "False", "true", "on", "0", " 1 "):
            with self.subTest(value=value):
                checker, instance, calls, _notices = load_method(value)
                self.assertEqual(checker(instance, "v0.0.0"), "v0.0.0")
                self.assertEqual(calls, [])

    def test_explicit_opt_in_checks_upstream_once(self):
        checker, instance, calls, _notices = load_method("1")
        self.assertEqual(checker(instance, "v0.0.0"), "v1.2.3")
        self.assertEqual(calls, [(UPSTREAM, 10)])

    def test_opted_in_network_failure_uses_fallback(self):
        checker, instance, calls, notices = load_method("1", fail=True)
        self.assertEqual(checker(instance, "v0.0.0"), "v0.0.0")
        self.assertEqual(calls, [(UPSTREAM, 10)])
        self.assertTrue(notices)


if __name__ == "__main__":
    unittest.main()
