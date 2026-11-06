# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Verify the actual imported metrics task fails closed before export setup.

The collector function is executed from its AST with only controlled fakes.
No Plane/Celery application, database, exporter, or network client is loaded.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / (
    "apps/api/plane/license/bgtasks/telemetry_metrics.py"
)


class ReachedExporterSetup(Exception):
    pass


def collector_for(instance):
    module = ast.parse(SOURCE.read_text())
    function = next(node for node in module.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "_collect_and_push_metrics")
    function.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    accesses = {"instance_reads": 0, "endpoint_calls": 0}

    def first_instance():
        accesses["instance_reads"] += 1
        return instance

    def endpoint():
        accesses["endpoint_calls"] += 1
        raise ReachedExporterSetup("Reached explicitly opted-in export path")

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("Exporter, meter or resource initialized without opt-in")

    namespace = {
        "Instance": SimpleNamespace(objects=SimpleNamespace(first=first_instance)),
        "logger": SimpleNamespace(debug=lambda *_args: None),
        "os": SimpleNamespace(environ={"OTLP_METRICS_PROTOCOL": "grpc"}),
        "get_otlp_grpc_endpoint": endpoint,
        "get_otlp_http_metrics_url": fail_if_called,
        "_create_otlp_metric_exporter": fail_if_called,
        "Resource": SimpleNamespace(create=fail_if_called),
        "PeriodicExportingMetricReader": fail_if_called,
        "MeterProvider": fail_if_called,
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["_collect_and_push_metrics"], accesses


class TelemetryMetricsOptOutTests(unittest.TestCase):
    def test_missing_instance_never_initializes_export(self):
        collector, counters = collector_for(None)
        self.assertIsNone(collector())
        self.assertEqual(counters, {"instance_reads": 1, "endpoint_calls": 0})

    def test_disabled_consent_never_initializes_export(self):
        collector, counters = collector_for(
            SimpleNamespace(is_telemetry_enabled=False)
        )
        self.assertIsNone(collector())
        self.assertEqual(counters, {"instance_reads": 1, "endpoint_calls": 0})

    def test_explicit_opt_in_reaches_metrics_setup(self):
        # The sentinel halts execution before an exporter or network client exists.
        collector, counters = collector_for(
            SimpleNamespace(is_telemetry_enabled=True)
        )
        with self.assertRaises(ReachedExporterSetup):
            collector()
        self.assertEqual(counters, {"instance_reads": 1, "endpoint_calls": 1})


if __name__ == "__main__":
    unittest.main()
