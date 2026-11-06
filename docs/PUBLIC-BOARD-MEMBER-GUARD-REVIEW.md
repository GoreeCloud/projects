# GoreeCloud Projects — Public board member disclosure gate

**Status:** Proposed and isolated-test validated on a draft branch, not merged or deployed.
**Source:** Attributed Plane-derived `apps/api/plane/space/views/project.py` (AGPL-3.0-only).

## Reason for this change

The public endpoint `anchor/<str:anchor>/members/` intentionally uses
`AllowAny` to provide a limited directory for people viewing a published
project board. The inherited handler resolved `DeployBoard` by *any* anchor,
without checking `entity_name`, `is_disabled`, `deleted_at`, or that
`entity_identifier` matched its `project_id`.

The modified handler resolves a board only when the exact anchor belongs to an
enabled, non-deleted *project* board with consistent project identity. Otherwise
it responds with 404 and does not look up member records.

This protects the member-list endpoint, **not every public board endpoint**.
The returned fields for a valid published board remain exactly the inherited
four fields: `id`, `member`, `member__display_name`, `member__avatar`.
Email addresses are not returned by this handler.

## Verification performed

- `python3 -m unittest discover -s tests -p 'test_public_board_members_guard.py' -v`:
  **2 tests passed** in a detached, clean worktree at
  `f7f6e920489e44878f597aab97ebf04eb17f565b`.
- The tests extract and execute the **actual endpoint method body** with a fake
  ORM query layer; they cover a valid board and invalid, wrong-entity,
  disabled, soft-deleted, and mismatched project anchors.
- `python3 -m compileall -q` succeeded for the edited view and new tests.

## Required before approval

1. Run a real Django and PostgreSQL integration test using only synthetic data.
   Confirm HTTP status, `DeployBoard` query semantics and disabled/deleted behavior.
2. Test a valid published board, a board whose publication has been disabled,
   deleted anchors, invalid anchors, and non-project entity anchors.
3. Audit **other `plane.space` public endpoints** independently. Several still
   resolve board anchors without an `is_disabled=False` filter. Do not claim
   unpublishing/revocation is globally enforced from this patch alone.
4. Review whether user display names, avatars and stable member IDs should be
   disclosed to anonymous viewers; consider minimized profiles or an explicit
   project-owner sharing policy and tests.
5. Test permissions for private workspace/project-member APIs, cross-tenant
   and inactive memberships. Verify the historical Plane advisory separately.
6. Obtain code review and complete standard release gates before merging or
   deploying. No production access or user data were used.

Tracking: https://github.com/GoreeCloud/projects/issues/6
