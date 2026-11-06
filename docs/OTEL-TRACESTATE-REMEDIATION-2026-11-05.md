# GoreeCloud Projects — OpenTelemetry security update

**Status:** development-only source patch, not merged, deployed or runtime-accepted.

## Source-grounded issue

The imported Plane backend pinned opentelemetry-api 1.28.1, affected by
[GHSA-xcq7-p3pf-p88h](https://github.com/open-telemetry/opentelemetry-python/security/advisories/GHSA-xcq7-p3pf-p88h)
(CVE-2026-114603, uncontrolled resource consumption in inbound tracestate
header parsing). The patched stable API starts at **1.45.1**.

## Coordinated dependency update

Updated the five direct pins in apps/api/pyproject.toml:

- opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp,
  opentelemetry-exporter-otlp-proto-grpc: 1.28.1 to 1.45.1
- opentelemetry-instrumentation-django: 0.49b1 to 0.66b1

The lockfile resolver coordinated the API/SDK/exporter versions at 1.45.1
and the instrumentation/semantic-convention versions at 0.66b1.
The update adds opentelemetry-exporter-http-transport and
opentelemetry-exporter-otlp-common, and removes unneeded dependencies.
Python 3.12 support is preserved.

## Verification

- Resolved with Plane-pinned uv 0.12.21; newer uv refused due to
  the repository's required-version policy.
- The global no-source-build resolver mode could not process zxcvbn==4.4.28.
  Its sdist checksum matched PyPI, and its setuptools build file was
  inspected before allowing isolated metadata resolution.
- The pinned uv lock --check passed.
- Post-update OSV querybatch scan covered **122 pinned PyPI packages**;
  only the earlier historical Plane member-disclosure advisory
  GHSA-87x4-j8vh-p5qf remains in the advisory results.
- Regression tests are at tests/test_otel_security_lock.py.

A public advisory match does not prove that the imported source is exploitable.

## Release blockers and acceptance

1. Run isolated Django/backend integration tests with the updated package set;
   verify middleware, tracing, metrics and OTLP exporter contracts.
2. Verify that the opt-out work proposed in PR #3 stays effective;
   no metrics should export when is_telemetry_enabled is false.
3. Audit runtime egress, dependencies, licenses and configuration;
   do not enable additional instrumentation by default.
4. Test controlled tracestate header input and ingress size limits.
5. Verify whether the historical Plane public member disclosure applies;
   require permission-denial and published-board member-data tests.
6. Do not release or deploy without applicable security, runtime,
   recovery and rollback acceptance.

Related tracking: https://github.com/GoreeCloud/projects/issues/6
