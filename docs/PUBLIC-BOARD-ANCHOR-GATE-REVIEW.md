# GoreeCloud Projects — shared project-board anchor security gate

**Status:** draft code change; not merged, deployed, or application-accepted.
**Import:** Plane-derived `apps/api/plane/space/views/base.py`; preserve inherited AGPL-3.0-only notices.

## Reason

The existing `DeployBoardAnchorMixin.initial` checked only for an inconsistent
`entity_identifier` on boards whose `entity_name` was `project`.
It did not reject unknown anchors, disabled boards, soft-deleted boards or
anchors for other entity types. Multiple anonymous-access project-board
views inherit this mixin.

The proposed guard requires each request with an `anchor` kwarg to resolve to
one matching project board with:

- `anchor` equal to the requested value;
- `entity_name="project"`;
- `is_disabled=False`;
- `deleted_at IS NULL`;
- `entity_identifier` equal to the related `project_id`.

If the board does not pass, `NotFound` is raised **before the handler runs**.
Routes without an `anchor` kwarg are left unchanged.

## Static URL coverage evidence

A read-only Python AST inventory of `apps/api/plane/space/urls/*.py`
identified **23 routes** containing `<str:anchor>`; all **23 handlers**
directly inherit `BaseAPIView` or `BaseViewSet`, which themselves include
`DeployBoardAnchorMixin`. `tests/test_public_board_route_coverage.py`
asserts this relationship and catches future handlers that bypass these
two base classes. It does not test Django URL dispatch or database behavior.

## Test evidence

- The isolated test extracts and executes the **actual mixin code** with a
  fake ORM implementing equality, null checks, and `F` comparisons.
- The fixture asserts valid boards pass, and missing, wrong-type, disabled,
  soft-deleted, or mismatched anchors are denied.
- It also verifies non-anchor routes continue without board lookup.
- `python3 -m unittest discover -s tests -p 'test_public_board*.py' -v`:
  **7 passing tests** on a detached branch checkout; Python syntax compilation
  passed and the test worktree was clean.

A second isolated test compiles the actual mixin method and executes its
`F("project_id")`, `deleted_at IS NULL` and `is_disabled=False` filters
against a real **Django 5.2.17 ORM**, with synthetic project-board rows in a
private **in-memory SQLite database**. Valid and invalid examples passed.
No Plane models, services, credentials or real data are loaded.

These are source-level and synthetic ORM tests, **not** a full Plane Django
or PostgreSQL HTTP acceptance test.

## Dependencies, risk, and release gates

1. Inventory every public URL backed by `BaseAPIView` and `BaseViewSet`;
   confirm each `anchor` represents a project board. Some published
   operations may intentionally use other entity-type anchors and must
   be explicitly reconciled, not silently broken.
2. Run anonymous and authorized HTTP tests in isolated Django/PostgreSQL,
   including missing, valid, disabled, deleted, mismatched, and other-type
   anchors; inspect status codes and response body privacy.
3. Confirm board disable/unpublish and soft-delete semantics across the entire
   API; some routes use `slug`/`project_id` **without an `anchor` kwarg**
   and will not be protected by this mixin.
4. Test repeated requests after revocation, caches, session teardown,
   public-board assets, issue comments, reactions, votes, and intake operations.
5. Review compatibility with the narrower public member endpoint fix in
   [PR #10](https://github.com/GoreeCloud/projects/pull/10).
6. Preserve attribution and release gates. Do not merge or deploy until
   acceptance; isolated tests do not prove that all outbound public content
   is access-controlled.

Tracking: https://github.com/GoreeCloud/projects/issues/6
