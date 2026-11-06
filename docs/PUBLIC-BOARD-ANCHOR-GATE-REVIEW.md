# GoreeCloud Projects — shared project-board anchor security gate

**Status:** draft code change; not merged, deployed, or application-accepted.
**Import:** Plane-derived `apps/api/plane/space/views/base.py`; preserve inherited AGPL-3.0-only notices.

## Reason

The existing `DeployBoardAnchorMixin.initial` checked only for an inconsistent
`entity_identifier` on boards whose `entity_name` was `project`.
It did not reject unknown anchors, disabled boards, soft-deleted boards or
anchors for other entity types. An enabled board could also remain reachable
if its parent project/workspace was soft-deleted or the board's stored workspace
did not match its project's workspace. Multiple anonymous-access project-board
views inherit this mixin.

The proposed guard requires each request with an `anchor` kwarg to resolve to
one matching project board with:

- `anchor` equal to the requested value;
- `entity_name="project"`;
- `is_disabled=False`;
- `deleted_at IS NULL`;
- its parent project and workspace both have `deleted_at IS NULL`;
- its `project__workspace_id` equals the board's `workspace_id`;
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

The same inventory confirms exactly **two URL patterns without an anchor**:

- `workspaces/<str:slug>/projects/<uuid:project_id>/anchor/` — anonymous
  anchor/settings lookup; [issue #6](https://github.com/GoreeCloud/projects/issues/6)
  tracks missing publication-state checks.
- `workspaces/<str:slug>/project-boards/` — anonymous workspace board listing;
  [issue #12](https://github.com/GoreeCloud/projects/issues/12) tracks the
  verified URL/view signature mismatch and invalid queryset access.

The added structural test detects newly introduced unanchored public routes.
**Neither route is secured by this anchor-mixin change.**

## Test evidence

- The isolated test extracts and executes the **actual mixin code** with a
  fake ORM implementing equality, null checks, and `F` comparisons.
- The fixture asserts valid boards pass, and missing, wrong-type, disabled,
  soft-deleted, or mismatched anchors are denied.
- It also verifies non-anchor routes continue without board lookup.
- `python3 -m unittest discover -s tests -p 'test_public_board*.py' -v`:
  **11 passing tests** on a detached branch checkout; Python syntax compilation
  passed and the test worktree was clean.

A second isolated test compiles the actual mixin method and executes its
`F("project_id")`, `deleted_at IS NULL` and `is_disabled=False` filters
against a real **Django 5.2.17 ORM**, with synthetic project-board rows in a
private **in-memory SQLite database**. Valid and invalid examples passed,
including deleted parent project/workspace and inconsistent tenant relationships.
No Plane models, services, credentials or real data are loaded.

An additional two tests instantiate a synthetic `APIView` with the actual
`DeployBoardAnchorMixin`, dispatch GET requests using **Django REST Framework
3.18.3** `APIRequestFactory`, and verify that a valid board returns HTTP
200 while missing, disabled, deleted, non-project and mismatched boards return
HTTP 404, including soft-deleted parent entities and cross-workspace
board records. A further test confirms that publication changes are checked
on every request: disabling a previously available board changes its next
response from 200 to 404; soft-deleting its project also denies the next
request. They execute on synthetic Django 5.2.17 SQLite rows without
production user/session models or an external exporter.

The combined local-only integration of draft PRs #3, #5, #7, #8, #10 and #11
passed **22/22 focused tests** and `uv lock --check` in a clean worktree.

These are isolated DRF-dispatch and synthetic ORM tests, **not** the full
Plane Django application on PostgreSQL, its actual URL router, reverse proxy,
or a deployed publication/revocation test.

## Full-application PostgreSQL contract tests (prepared, not executed)

`apps/api/plane/tests/contract/app/test_public_board_publication_boundary_app.py`
adds **9 intended test cases** to the project's existing `pytest-django`
suite, using real `plane.db.models`, Django URL routing, DRF middleware,
and the application's `session_client` and `workspace` fixtures.
They cover disabled, deleted, parent-deleted, cross-workspace and anonymous
access to published project-board routes, plus next-request revocation.

The file was compiled, AST-inspected, and read back successfully in a clean,
detached source worktree; its tests were **NOT run**. The authorized laptop
has no PostgreSQL test server and its existing minimal isolated environment
does not contain the full Plane application dependencies. **Do not include
these nine cases in any passing isolated-suite test count.**

For a future authorized isolated Plane/PostgreSQL test environment, run this
target file under the existing `apps/api/pytest.ini` and
`plane.settings.test` configuration with only disposable test data, no
production credentials, and blocked outbound network access. Compare failures
against the source baseline and test permissions before accepting the PR.

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
