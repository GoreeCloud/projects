# GoreeCloud Projects — temporary fail-closed public-board discovery

**Status:** proposed source-level security mitigation, not a release or deployment.
**Source:** attributed Plane import, AGPL-3.0-only; existing upstream notices are retained.

## Risk and decision

Two inherited anonymous URL routes can be reached without an explicit publication
anchor or authenticated tenant authorization:

- `workspaces/<str:slug>/project-boards/` — handler previously expected the
  wrong kwarg and referenced a queryset method without calling it, causing
  errors; blindly repairing it would enable enumeration of published projects
  in a guessed workspace.
- `workspaces/<str:slug>/projects/<uuid:project_id>/anchor/` — historical
  publication anchor discovery did not check whether publication was currently
  enabled, deleted, revoked, or workspace-consistent.

Until deliberate anonymous listing, revocation, consent, serialization and
tenant boundaries are accepted, these two URLs return only a generic **404**,
with no ORM query. They are **intentionally unavailable**, including for
otherwise public projects. This is a temporary availability tradeoff to
avoid exposing potential cross-tenant data or publication capabilities.

Existing `anchor/<str:anchor>/...` routes are **not changed** by this
patch. Their own validation and privacy controls must be fixed and
verified separately. This gate does not make those other routes safe.

## Verification and follow-up

- Python standard-library tests assert Django URL signatures match the
  handlers, the handler bodies are single unconditional 404 responses,
  and the *actual extracted source methods* return generic 404 without
  loading Plane, a database or user data.
- A pinned, least-privilege, nonpublishing CI workflow runs the test on PR
  and matching main changes; its real outcome must be verified separately.
- The broader [anonymous publication patch PR #19](https://github.com/GoreeCloud/projects/pull/19)
  remains a draft. Reintroducing public discovery requires source-reviewed
  full Plane/PostgreSQL HTTP authentication/authorization tests, published-only
  serializer minimization, revoked/deleted tenant tests, cache invalidation,
  GoreeShield consent and compatibility decisions, and safe release controls.
- This change does **not** start Plane, provision test PostgreSQL, change
  backups, migrate user content, deploy, or alter credentials.

Track issues [#12](https://github.com/GoreeCloud/projects/issues/12) and
[#6](https://github.com/GoreeCloud/projects/issues/6) as **still open**.
