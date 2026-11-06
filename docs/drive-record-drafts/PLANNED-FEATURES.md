# GoreeCloud Projects — Planned Features (Draft)

**Prepared:** November 5, 2026.
**Status:** NONCANONICAL GITHUB REVIEW DRAFT — not a released roadmap or accepted deployment.
**Intended authoritative destination:** `GoreeCloud/Projects/GoreeCloud Projects/PLANNED-FEATURES.md`.

## P0 — Safe release foundation

1. Complete AGPL and third-party trademark/asset/license checks. Preserve Plane Software, Inc. and contributors' notices; determine lawful replacement assets.
2. Accept explicit opt-in telemetry from [PR #3](https://github.com/GoreeCloud/projects/pull/3). Verify migration on isolated PostgreSQL databases, negative/duplicate consent cases, browser retry, and an actual metrics-off egress trace; existing opt-ins must not change silently.
3. Accept JavaScript and Python security updates only after full dependency integrity and build/test compatibility reviews. Current draft PRs [#5](https://github.com/GoreeCloud/projects/pull/5) and [#8](https://github.com/GoreeCloud/projects/pull/8) are not merged. Review remaining `minimatch` major-version compatibility and historical Plane member-disclosure applicability.
4. Verify private workspace/project/member permissions, revocation, CSRF/session security, secret management, rate limits, network allowlists, logs, synthetic data recovery, and backup restore.
5. Design and enable only reviewed CI with least-privilege permissions, locked dependencies, security scans, isolated test infrastructure and rollback evidence.
6. Demonstrate working application across browser, admin API and public-board routes; accept keyboard navigation, screen reader behavior, contrast, responsiveness, error states and performance.

## P1 — GoreeCloud UI and product identity

- Apply approved GoreeCloud UI tokens, accessible components, responsive layouts and theme controls without blindly replacing upstream compatibility contracts.
- Replace Plane-branded icons, PWA assets, social links, copy and screenshots with rights-cleared original GoreeCloud assets.
- Produce rendered light/dark and mobile/desktop acceptance evidence. The active design standard does not imply the imported Plane UI has passed it.

## P1 — Workspace Teams and Tasks integration

- **Teams = communication**, **Projects = project execution**, **Tasks = intended canonical shared task identity**.
- Begin with permission-checked, **read-only issue deep links**, preserving membership and revocation across project boundaries.
- Define identity federation or trusted OIDC, scoped organization/project/member roles, stable external IDs and audit provenance.
- Introduce a separately reviewed shared Tasks API only after GoreeCloud Tasks has a server-backed canonical record. Existing Tasks clients currently store local-only data.
- Define deterministic field ownership, idempotent events, retry and dead-letter handling, tombstones, authorization at read/write time, rollback, conflict resolution and a controlled migration. Avoid two-way dual writes and direct cross-service database access.

## P2 — Project execution enhancements

- GitHub commit/issue/PR and CI associations, task-level dependency tracking, milestones, cycle forecasting, work-item templates and source-linked release evidence.
- Optional GoreeCloud Manager read-only health, GoreeCloud Notify opt-in events, and GoreeCloud AI suggested triage with explicit approval gates.
- Import/export, recovery, observability and measurable quality/performance budgets for self-hosted environments.

## Exit criteria

No feature is described as released until built, tested, authorized, observable and documented against the live repository and authorized deployments. Avoid assigning invented timelines or claiming continuous background execution. Track blockers in GitHub and Todoist, and reconcile this record into the canonical Drive folder through a verified in-place/upload workflow.
