# GoreeCloud Projects — Telemetry opt-in acceptance

**Status:** change proposal on a development branch; not merged, deployed, or release-accepted.
**Upstream:** Plane preview import. Inherited code remains licensed AGPL-3.0-only.

## Behavior

- New instances start with telemetry disabled in the model, UI, and a non-destructive additive migration.
- The setup endpoint accepts a **single explicit affirmative POST value** only; absent, false, ambiguous, or duplicated fields do not enable collection.
- Failed first-run form submissions do not regain telemetry consent via redirect query parameters.
- The existing OTLP metrics task already checks the stored `is_telemetry_enabled` field before exporting.
- Existing instances with telemetry enabled remain enabled until an authorized administrator changes them. Changing a model default is not a retroactive privacy migration.

## Review and tests

Source-reviewed acceptance checks: parsing, single-field requirement, model/UI defaults, preservation of earlier migrations, and existing metrics export gate.

Dependency-free regression tests can run as:

```sh
python3 -m unittest discover -s tests -p 'test_telemetry_consent.py' -v
python3 -m py_compile apps/api/plane/license/telemetry_consent.py apps/api/plane/license/migrations/0007_default_telemetry_opt_out.py
```

**Still required before merging or deploying:** execute the above against an actual checked-out branch; run Django migration checks against both fresh and existing synthetic databases, verify cross-version migration behavior, test admin setup and retries in a browser, verify Celery/OTLP traffic is absent for opted-out instances, inspect network egress from licensing/version checks, and run the full upstream backend/UI test suites in an isolated environment after reviewing dependencies.

## Non-goals

This change does not disable unrelated outbound traffic or network-based licensing, does not change real users' existing preferences, does not guarantee no personal information ever leaves the server, and does not finish the GoreeCloud UI rebrand or the Workspace Teams / Tasks integrations.

Do not promote this branch to production solely because unit/static checks pass.
