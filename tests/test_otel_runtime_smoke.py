# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Isolated imports and local-only metrics check; never configure a network exporter."""
import importlib.util
import time
import unittest
from importlib.metadata import version


class OpenTelemetryRuntimeSmokeTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("opentelemetry") is not None, "OpenTelemetry not installed")
    def test_imported_metrics_symbols_and_bounded_tracestate(self):
        from opentelemetry import metrics
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GrpcExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter as HttpExporter
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.trace.span import TraceState

        self.assertEqual(version("opentelemetry-api"), "1.45.1")
        self.assertEqual(version("opentelemetry-sdk"), "1.45.1")
        self.assertEqual(version("opentelemetry-instrumentation-django"), "0.66b1")
        for symbol in (MeterProvider, PeriodicExportingMetricReader, Resource, GrpcExporter,
                       HttpExporter, DjangoInstrumentor):
            self.assertTrue(callable(symbol))
        # No exporter or reader is configured: this cannot transmit telemetry.
        provider = MeterProvider(resource=Resource.create({"service.name": "goreecloud-isolated-test"}))
        try:
            provider.get_meter("goreecloud.smoke").create_counter("local_checks").add(1)
        finally:
            provider.shutdown()

        start = time.perf_counter()
        TraceState.from_header(" " * 9000)
        self.assertLess(time.perf_counter() - start, 2.0)


if __name__ == "__main__":
    unittest.main()
