# GoreeCloud Projects — Four Anonymous Board Route Acceptance (Draft)

**Status:** Source-level security patch stacked on the **unmerged** Projects PR #19;
not a production acceptance, upstream Plane deployment, license/legal review, or
release approval. Original Plane copyrights, AGPL-3.0-only source notices and
third-party rights remain in effect.

## Scope

The exact anonymous routes tested against isolated Django/DRF synthetic models:

- Workspace public project listing, scoped by the workspace slug
- Workspace project anchor lookup, scoped by slug and project UUID
- Public board settings by published anchor
- Active public project members by published anchor

All four must honor current, non-disabled, non-deleted **project** publications
with matching entity identifier, project/workspace ownership, live project
and live workspace. A revoked or mismatched anchor must not show settings or
the limited member directory merely because an old URL exists. The member
directory still returns the inherited limited id/member/display-name/avatar
fields when the underlying publication is valid; this is **not** a decision
that every profile field is privacy-appropriate for public viewers.

## Reproducible local and CI checks

The existing exact lockfile-derived, SHA-256-hashed five pure wheels enable
the test-only Django and DRF runtime. Source-contract tests assert exact
live-publication query predicates and route signatures. The disposable,
in-memory SQLite models exercise actual extracted view methods through DRF
request dispatch, including publication revocation, deleted entities,
workspace mismatch and public projection.

This isolated harness intentionally substitutes Plane's BaseAPIView and
its model schema with minimal synthetic equivalents. It does **not** run
full Plane startup, migrations, PostgreSQL, real tenant permissions,
cached/reverse-proxy responses, browser/member UI, profile consent, auth
lifecycle, logging, or production access. Additional anonymous Space
routes (issues, cycles, modules, states, labels and metadata) require a
separate full-app source and authorization review. Keep this feature branch
draft until those gates and intersecting PRs #10, #11, and #18 are reconciled.

No production service, database, DNS, identity, public endpoint or user data
is modified by this test-first development patch.

## November 14, 2026 — disposable PostgreSQL query check (source-review branch)

A **second, independent GitHub Actions job** now runs the same synthetic
Django/DRF view-method regression cases against an ephemeral PostgreSQL 17
service. The `GC_PUBLIC_BOARD_BACKEND=postgres` selection uses a fixed local
test-only database/user/password rather than an operator-supplied connection
string, and a new regression asserts that the selected PostgreSQL backend was
actually used (not a silently substituted SQLite database).

- PostgreSQL Official Image `17-alpine` is pinned to OCI index digest
  `sha256:d3244e8ce3f165ee3c93d9c4a4b1d0fe48b3a89e2287b717fdcbbde92d405065`.
- The Python 3.12 PostgreSQL driver wheels (`psycopg`, `psycopg-binary`
  and `typing-extensions`) use exact `apps/api/uv.lock` versions and
  SHA-256 hashes with no dependency resolution.
- The SQLite and PostgreSQL jobs execute separately and **both must pass**.
- [PostgreSQL and SQLite CI run 43603273233](https://github.com/GoreeCloud/projects/actions/runs/43603273233)
  succeeded at PR source commit `fd4baedde3bd176d20dd5eb6eda6320d9c107925`.
  The same source-only credential preflight was independently green before
  this documentation update.

**Scope remains limited:** PostgreSQL is a real, isolated database engine, but
the models, query harness and base classes are synthetic substitutes. This
does **not** run the imported Plane application, full migrations, production
authorization, real tenants, external caches, identity policies, full route
mapping or publication consent. Do not merge or deploy this draft solely
because PostgreSQL synthetic query tests are green.
