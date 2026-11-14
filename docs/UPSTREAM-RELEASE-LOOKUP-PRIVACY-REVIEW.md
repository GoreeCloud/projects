# GoreeCloud Projects — upstream release lookup privacy gate

**Status:** source-level privacy safeguard; production/runtime acceptance remains open. A previous draft proposed this gate; current-main integration is tracked separately.
**Source:** attributed Plane import, AGPL-3.0-only.

## What changed

The imported `register_instance` management command makes a network request to
`https://api.github.com/repos/makeplane/plane/releases/latest` to discover
the upstream version. This request is independent from the metrics/telemetry
consent flag and can occur during initial instance setup.

The version checker now returns the locally determined fallback version
**without a network request by default**. A server administrator may explicitly
enable this specific upstream release query by setting:

`GOREECLOUD_ALLOW_UPSTREAM_RELEASE_CHECK=1`

Only the exact string `1` enables the request. Missing, malformed, or
non-affirmative values fail closed. A checked network request still uses the
imported upstream Plane releases URL with a 10-second timeout, and HTTP errors
still fall back to the local version. No alternate GoreeCloud release service
or update protocol is invented.

This opt-in is separate from `is_telemetry_enabled`; consenting to metrics
must not silently enable third-party release checks.

## Isolated validation

`tests/test_upstream_release_opt_in.py` extracts and executes the **actual
imported version-check method body** with a fake environment and fake
`requests.get`. It asserts:

1. Default/missing and malformed choices do not invoke HTTP at all.
2. Exact opt-in makes one request to the expected upstream URL with timeout 10.
3. Opted-in HTTP failure retains the local fallback behavior.

An earlier draft reported **3/3** isolated tests passing. Current-branch
CI and post-merge evidence must be verified separately. No actual network, Celery, application startup,
production database, credentials, or user account was used.

## Remaining release acceptance

- Audit all independent network egress paths in the Plane-derived application,
  including CDN resources, analytics, telemetry and setup helpers. This patch
  changes **only one** upstream-version request.
- Verify the exact environment variable is documented in the actual supported
  self-host installer and container/deployment configuration before releasing.
- Test registration, server upgrades and version display in a fully isolated
  Django/PostgreSQL installation, with outbound network restricted by policy.
- Decide whether and how the GoreeCloud product should check for its **own**
  release versions rather than the imported Plane release feed.
- Obtain privacy, compatibility, licensing, security and rollback review.

Related: telemetry default-off draft PR #3 and privacy/security issue #2.

## Integration provenance

This implementation carries forward the bounded change from [earlier draft PR #13](https://github.com/GoreeCloud/projects/pull/13) on top of the current main branch, preserving the current GoreeCloud OpenRoom product name and prior security changes. The new read-only privacy workflow exercises the reviewed, isolated method-body tests. It does not assert that metrics or any other external network calls are disabled.
