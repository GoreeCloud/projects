# Projects — Additional Anonymous Anchor Routes (Draft)

**Status:** Source-level draft stacked on the unmerged Projects public-board
feature branch. AGPL-3.0-only Plane authorship and notices remain unchanged;
this is not full Plane/PostgreSQL or production authorization acceptance.

## Five additional inherited anonymous readers

The Space project router defines anchor-based cycles, modules, states, labels
and meta endpoints in five independent view modules. Previously
cycles/modules/states/labels selected an arbitrary DeployBoard anchor
(without checking even project entity type), while metadata required only
an entity name of project. Stale, disabled, soft-deleted or mismatched
anchors could still select data after a project stopped being published.

This patch uses the same current project-board publication predicates on
all five routes: matching entity_identifier and project ID, project entity
type, enabled and nondeleted board, live project/workspace and matching
workspace ownership. Unpublished anchors return HTTP 404 before reading
the downstream project records. Valid published list shapes and Triage
exclusion in the state reader are retained.

Two new executable tests extract the five actual Django/DRF view methods
and test disposable synthetic SQLite models: valid scoped records, an
unrelated workspace, unknown anchor, board disabling/soft deletion, wrong
entity/identity, deleted project/workspace and ownership mismatch. Two AST
contract tests assert exact route signatures and publication predicates.

## Security/release boundaries

These tests deliberately replace inherited Plane BaseAPIView and models;
they do not exercise imported Plane services, PostgreSQL, permission policy,
proxy caches, tenant credentials, UI, database migrations or deployment.
Additional anonymous Space issues, intake, assets and other routings still
need independent full-product review. Approval of publicly shared project
data and GoreeShield consent/minimization remains open.

No live database, user content, production instance, network or identity
configuration is read or changed by this source-only proposal.
