# GoreeCloud Projects — public issue publication revocation (draft)

**Status:** source-level security mitigation stacked on unmerged Projects
PR #19. This does NOT prove production authorization or Plane PostgreSQL
acceptance. Inherited Plane copyrights and AGPL-3.0-only license remain.

## Finding and scoped mitigation

The public Space project listing, anchor discovery, settings, members,
cycles, modules, states, labels and metadata routes already check current
publication state. But the public issue list, issue detail and public
comment/reaction/vote handlers previously resolved boards by historical
anchor alone. Revoked, disabled, deleted, wrong-entity or
ownership-mismatched boards could still reach those issue operations.

The shared source-owned helper in issue.py now requires the current
anchor, project entity, entity identifier equal to project ID, enabled
and non-deleted board, active project/workspace and identical
project/workspace ownership before returning any board. All fifteen
issue/interaction lookups reuse that guard; absent/revoked lookups
continue to use the pre-existing first() or get() not-found behavior.

The reaction/vote list handlers no longer use slug/project_id URL
kwargs that are absent from their anchor-based routes. They resolve
the reviewed board first, then scope lists to its actual workspace
and project. This is a correctness and privacy fix, not permission
to publish arbitrary issue, account or attachment details.

## Evidence and remaining gates

Source-contract tests inspect the actual issue.py AST and require exact
guard query predicates, no unguarded direct DeployBoard manager use,
board checks before issue fetching, and correct anchor-based reaction/
vote scope. The existing disposable Django/DRF SQLite test harness
extracts the actual helper and checks valid publication, disabled,
deleted, wrong entity/identifier, project/workspace deletion and
foreign workspace mismatch. Those tests do not initialize Plane.

Release requires real PostgreSQL/Plane migrations, end-to-end tenant
permissions, cache/CDN revocation, issue-level private/draft/archived
visibility checks, serializer minimization for comments/assignees/
attachments, authenticated write permission review, account lifecycle,
GoreeShield privacy, Wardveil controls, GC UI/accessibility, licensing,
staged deployment and rollback validation. No live accounts, database,
DNS or VPS assets are changed by this draft patch.
