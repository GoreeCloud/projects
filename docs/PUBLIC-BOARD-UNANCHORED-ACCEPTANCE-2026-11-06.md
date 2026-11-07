# GoreeCloud Projects — unanchored public-board route release gates

**Status:** RED / unresolved — source-contract checks are expected to fail.
**Date reviewed:** November 6, 2026.
**Source authority:** attributed Plane import in `GoreeCloud/projects`.
**Product authority:** canonical GoreeCloud Drive Projects records.
**Deployment:** no production changes, route edits, merges or public release.

## Release-blocking routes

The imported Space API exposes two anonymous routes without an `anchor`
keyword argument, which means draft shared-anchor-guard PR #11 does not
authorize either:

| Route | Handler | Exposure / defect |
| --- | --- | --- |
| `workspaces/<str:slug>/project-boards/` | `WorkspaceProjectDeployBoardEndpoint` | URL sends `slug`, handler expects `anchor`; a bare `.values_list` method is assigned instead of a board/queryset; the publication, soft-deletion and tenant filters are absent |
| `workspaces/<str:slug>/projects/<uuid:project_id>/anchor/` | `WorkspaceProjectAnchorEndpoint` | The anonymous lookup identifies boards by workspace/project but does not require `is_disabled=False`, an undeleted board/project/workspace, or consistent tenant ownership |

These are **source findings**, not a claim that the endpoints were
exploited or that an HTTP request to a deployed instance succeeded.

## Deliberately red acceptance checks

`acceptance/pending_public_board_routes.py` is a Python-standard-library
AST-based gate with exactly four checks, run explicitly via:

```sh
python3 -m unittest discover -s acceptance -p pending_public_board_routes.py -v
```

It is **outside** the passing `tests/` isolated smoke suite to avoid
reporting a known-broken release gate as a green development test.

The four gates require:

1. Workspace-board listing URL kwargs and handler parameters agree.
2. Workspace-board listing does not accidentally treat a bare
   `.values_list` method as a result.
3. Anonymous board enumeration is either **unconditionally denied** or
   requires published, enabled, non-deleted, workspace-matched project
   boards, with an explicit workspace slug constraint.
4. Anonymous workspace/project anchor lookup is either **unconditionally
   denied** or checks publication, deletion, identifier and tenant constraints.

A direct first-statement `raise NotFound()` or `raise Http404()` is
accepted as an interim fail-closed implementation; a nested or conditional
404 **does not** pass that exception. The code checks same-method direct
query keywords. A future implementation that delegates to a reviewed
helper/service may require a reviewed update to the static acceptance
logic plus **runtime tests**. These checks alone cannot certify safe
authorization.

## Verified current result

The exact committed test source `33be4455dbb6cc1a1dc2e66aefcf08f6662b2eb1`
was syntax-compiled and executed against the live imported route and view
source in a detached, clean local checkout.

**4 tests ran; all 4 failed as expected.** This proves four current
release gates remain unsatisfied. A nonzero exit status is an accurate
security-development finding, **not** a passing application test.

The two endpoint implementations were **not edited**. A previously
safety-blocked source modification must not be bypassed through an
alternate tool or new branch.

## Acceptance path

- Confirm intended product behavior for workspace board lists. Prefer
  authenticated access or an explicit, independently verified publication
  capability; the mere workspace slug must not authorize private project
  enumeration.
- Resolve the handler mismatch and invalid queryset use while maintaining
  exact response privacy and predictable 404s.
- If anonymous publication remains supported, check board, parent project,
  parent workspace, cross-tenant relationships, enablement, revocation and
  disabled/soft-deleted state at **every request**, not just at creation.
- Avoid returning anchor tokens, private work-item fields, emails, member
  lists, internal IDs, or detailed error distinctions to unauthorized users.
- Run isolated full-application Django/PostgreSQL HTTP tests for normal,
  anonymous, inactive-member and cross-workspace clients. The nine prepared
  contract cases in draft PR #11 are **still unexecuted**.
- Verify caching, browser/router behavior, clean teardown and revocation
  across supported public endpoints before merging or releasing.
- Get any previously safety-blocked edit reviewed through the appropriate
  approval mechanism. This review-only branch does not authorize that edit.

Related: [issue #12](https://github.com/GoreeCloud/projects/issues/12),
[issue #6](https://github.com/GoreeCloud/projects/issues/6),
[shared-anchor-guard draft PR #11](https://github.com/GoreeCloud/projects/pull/11).

The separate PostgreSQL 17 synthetic predicate fixture in PR #11 has
passed; it tests intended SQL against temporary tables, **not** these
unanchored handler contracts or the full Plane application.
