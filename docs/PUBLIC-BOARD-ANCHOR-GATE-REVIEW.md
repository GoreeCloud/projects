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

## Test evidence

- The isolated test extracts and executes the **actual mixin code** with a
  fake ORM implementing equality, null checks, and `F` comparisons.
- The fixture asserts valid boards pass, and missing, wrong-type, disabled,
  soft-deleted, or mismatched anchors are denied.
- It also verifies non-anchor routes continue without board lookup.
- `python3 -m unittest discover -s tests -p 'test_public_board_anchor_gate.py' -v`:
  **3 passing tests** on a detached branch checkout; Python syntax compilation
  passed and the test worktree was clean.

These are source-level logic tests, **not** a Django or PostgreSQL HTTP test.

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
