# GoreeCloud Projects — Competitive Objectives (Draft)

**Prepared:** November 5, 2026.
**Status:** NONCANONICAL GITHUB REVIEW DRAFT — product objectives, not existing competitive feature claims.
**Intended authoritative destination:** `GoreeCloud/Projects/GoreeCloud Projects/COMPETITIVE-OBJECTIVES.md`.

## Positioning

GoreeCloud Projects is intended as a **privacy-minded, self-hostable project execution system** built on an attributed Plane open-source derivative.

The ecosystem intentionally separates related jobs:

- **GoreeCloud Projects:** project plans, work items, cycles, modules, dependencies, roadmaps, release evidence and delivery.
- **GoreeCloud Workspace Teams:** discussion, channels, files and collaboration.
- **GoreeCloud Tasks:** future canonical shared task identity, assignment and priority, after a server-backed API and verified migrations exist.

This separation should avoid duplicate notifications, task copies and competing sources of truth. It is an **architectural objective**, not a current integrated capability.

## Differentiation objectives

| Dimension | Target advantage | Evidence needed |
| --- | --- | --- |
| Owner control | Practical self-hosting, data export and straightforward recovery without dependence on a proprietary hosted workspace. | Tested install, backup/restore, egress disclosure and recovery exercises |
| Privacy and security | Explicit opt-in metrics, least privilege, private-by-default projects and auditable membership boundaries. | Consent, authorization and network tests; pending PR review |
| Execution focus | Clear cycle/module/project views and evidence-backed release readiness. | End-to-end browser/API acceptance of inherited Plane functionality |
| Ecosystem cohesion | Contextual links with Teams, canonical future Tasks and optional GitHub/Manager/Notify integrations. | Versioned contracts, scoped identity, duplicate-write prevention and real integration tests |
| Premium usability | Consistent, accessible GoreeCloud UI and responsive layouts with helpful empty, loading and failure states. | Rendered a11y, keyboard, theme, contrast and responsive reviews |
| Open-source stewardship | Accurate AGPL-3.0-only attribution, security-maintained derivative and reproducible source/CI practices. | License review, secure upstream update process and source publication obligations |

## Guardrails

- Do **not** describe work item collaboration, AI integration, Teams links or task synchronization as live unless verified.
- Do **not** present user data privacy, external traffic behavior, audit completion or deployment readiness as certified based on source review alone.
- Do **not** claim an upstream Plane trademark, logo or media right solely from the software license.
- Avoid unsupported parity claims against products such as Plane, Jira, Linear, GitHub Projects or Asana; objective comparisons require current evidence and testable criteria.

## Suggested measurable acceptance benchmarks

- Unauthorized users cannot read private work-item or member data; membership revocation blocks all subsequently attempted reads and writes.
- Consent-off state performs **zero instance-metrics exports** in controlled tests; any unrelated external traffic is separately disclosed and restricted.
- Import/export and rollback retain task IDs, authorization metadata and issue history without silent duplication.
- A supported self-host installation and restore are repeatable from pinned, documented source.
- UI components pass the active GoreeCloud design standard's visual, accessibility and performance gates.

GoreeCloud Drive remains the final documentation authority. GitHub PR and application runtime state must be rechecked before approving this draft as a canonical record.
