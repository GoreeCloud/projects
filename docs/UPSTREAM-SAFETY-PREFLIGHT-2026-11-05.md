# GoreeCloud Projects — upstream security and release preflight

**Review date:** 2026-11-05
**Repository:** [GoreeCloud/projects](https://github.com/GoreeCloud/projects)
**Imported from:** [makeplane/plane](https://github.com/makeplane/plane), `preview` at `618d0eb74658329a6f6e92434ac54231422c5b96`.
**Disposition:** development-only; **deployment blocked** pending security, privacy, dependency, and runtime acceptance.

## Confirmed scope and provenance

- This is an attributed Plane derivative governed by `LICENSE` and `LICENSE.txt` (AGPL-3.0-only); `COPYRIGHT.txt` and upstream source headers are preserved.
- The upstream README is retained in `docs/UPSTREAM-README.md`.
- Ten inherited workflows are archived in `docs/upstream-github-workflows/` and none is active in `.github/workflows/`.
- The imported application has not been installed, built, migrated, or deployed as GoreeCloud Projects.
- A bounded import-time scan found two synthetic-looking key patterns in an upstream UI placeholder and an API documentation sample. This is **not** a comprehensive secrets or vulnerability audit.

## Highest-priority findings

| Priority | Area | Source-grounded observation | Required verification / mitigation |
| --- | --- | --- | --- |
| P1 | Telemetry opt-in | `apps/api/plane/license/models/instance.py` defaults `is_telemetry_enabled` to `True`. `apps/admin/components/instance/setup-form.tsx` also defaults the checkbox to `true`. | Make new installations opt-out, verify the consent flow and the persisted database default with isolated migrations and browser tests. |
| P1 | Consent parsing | `apps/api/plane/license/api/views/admin.py` reads `request.POST.get("is_telemetry_enabled", True)` without an explicit Boolean parser. | Parse affirmative consent explicitly; test the POST values `True`, `False`, missing and malformed. |
| P1 | External network behavior | The imported application includes an OTLP metrics job and a Plane release lookup in its instance-registration command. | Audit all outbound requests, configuration defaults and licensing flows separately; a metrics opt-out alone does not prove zero egress. |
| P1 | Deployment security | Multi-service application has unverified identity, tenancy, credentials, internal APIs, configuration and recoverability for GoreeCloud. | Use isolated test data, review service-to-service authentication and authorization, test backup/restore and least privilege before hosting. |
| P1 | Trademark and asset rights | Web metadata includes partial GoreeCloud naming; other manifests, images, screens and upstream links retain Plane branding. | Identify rights and replace brand-bearing assets with authorized GoreeCloud UI artwork; retain lawful source attribution and notices. |
| P2 | Dependency and workflow integrity | Full imported monorepo carries third-party runtime dependencies and ten upstream CI workflows, currently archived. | Audit pinned dependency manifests and setup hooks before any installation; enable only reviewed and least-privileged CI. |
| P2 | Cross-product records | GoreeCloud Tasks and Workspace Teams are not integrated with the imported Plane database. | Define task IDs, source-of-truth boundaries, scoped identity and link-only integration before any write synchronization. |

## Evidence limits

This review used source inspection, import manifest and license readback, and static search.
No Django migration tests, browser runtime tests, dependency installation, live network traces,
secret-scanning certification, or deployment verification are claimed.
Existing persisted telemetry preferences would not automatically be changed by altering
a Django field default; migration and consent handling need separate acceptance.

## Safe next actions

1. Prepare a reviewed privacy patch: explicit opt-in, secure parsing, additive migration and focused tests.
2. Run all tests in an isolated environment without production credentials; verify migration and telemetry-off network behavior.
3. Review upstream identity/license endpoints, dependencies, asset provenance, and security configuration.
4. Replace public-facing brand assets and page metadata only with approved GoreeCloud UI assets.
5. Define a read-only, permission-filtered Workspace Teams issue-link integration.
6. Record verified improvements in the canonical Drive index when supported by an in-place authorized edit.

Do not describe this document as a release certificate or a completed security audit.
