# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Dependency-free telemetry consent regression tests for the imported Plane app."""

import ast
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONSENT = ROOT / "apps/api/plane/license/telemetry_consent.py"
spec = importlib.util.spec_from_file_location("telemetry_consent_to_test", CONSENT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TelemetryConsentTests(unittest.TestCase):
    def test_explicit_affirmative_consent(self):
        for value in (True, "True", "TRUE", " true ", "1", "on", "ON"):
            with self.subTest(value=value):
                self.assertTrue(module.telemetry_opt_in(value))

    def test_missing_negative_or_malformed_values_fail_closed(self):
        for value in (None, False, "", "False", "false", "0", "off", "no",
                      "yes", "maybe", 1, 0, [], {}, ["True"], b"True"):
            with self.subTest(value=value):
                self.assertFalse(module.telemetry_opt_in(value))

    def test_source_integration_contracts(self):
        model = (ROOT / "apps/api/plane/license/models/instance.py").read_text()
        view = (ROOT / "apps/api/plane/license/api/views/admin.py").read_text()
        form = (ROOT / "apps/admin/components/instance/setup-form.tsx").read_text()
        migration = (ROOT / "apps/api/plane/license/migrations/0007_default_telemetry_opt_out.py").read_text()
        self.assertIn('is_telemetry_enabled = models.BooleanField(default=False)', model)
        self.assertIn('request.POST.getlist("is_telemetry_enabled")', view)
        self.assertIn('len(telemetry_values) == 1 and telemetry_opt_in(telemetry_values[0])', view)
        self.assertIn("  is_telemetry_enabled: false,", form)
        self.assertNotIn("isTelemetryEnabledParam", form)
        self.assertIn("field=models.BooleanField(default=False)", migration)
        ast.parse(view)
        ast.parse(model)
        ast.parse(migration)


if __name__ == "__main__":
    unittest.main()
