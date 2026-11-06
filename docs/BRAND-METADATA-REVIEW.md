# GoreeCloud Projects — shared browser metadata review

**Status:** development-only draft; source metadata and isolated tests, not deployed.
**Canonical product name:** GoreeCloud Projects (confirmed by the repository and
authoritative GoreeCloud Drive project records).
**Upstream provenance:** Plane Software, Inc. and contributors; AGPL-3.0-only
headers retained.

## Scoped work

The imported `packages/constants/src/metadata.ts` still supplied Plane
marketing strings to the root web page via `SITE_DESCRIPTION`. The selected
browser title and PWA manifest names had already been addressed in draft PR #7,
but that shared description remained generic/upstream-branded.

This patch adjusts only **display copy**:

- `SITE_NAME`, `SITE_TITLE` and `SITE_DESCRIPTION` identify GoreeCloud
  Projects and the project-execution functionality evidenced in imported source.
- Public-board `SPACE_SITE_NAME`, `SPACE_SITE_TITLE`, and
  `SPACE_SITE_DESCRIPTION` are labeled GoreeCloud Projects Public Boards.
- Unverified Twitter/X account identifiers are emptied rather than claiming a
  GoreeCloud-owned social profile.
- The original upstream source copyright and AGPL license notices remain.

The metadata exports are still maintained in the upstream-compatible
`@plane/constants` package. Renaming that package is a separate build and
dependency migration and is **not** part of this change.

## Explicit unresolved external-origin risk

`SITE_URL` and `SPACE_SITE_URL` still point to the inherited
`https://app.plane.so/` address. A bounded in-repository source reference
check on November 5, 2026 found only their definitions, not active consumers.
They were **not replaced with invented GoreeCloud URLs**.

These values require product-origin and build/consumer verification before any
published web app or social/canonical metadata is accepted. Do not assume that
the brand title edit changes redirects, embedded links, or third-party network
requests elsewhere in the application.

The inherited favicon, apple-touch-icon images, OG image, PWA icons and other
Plane media are **not rights-cleared GoreeCloud assets**. They still require a
separate licensing, asset replacement, rendering and compatibility review.
No full GoreeCloud UI design-system migration is claimed.

## Isolated validation

In a clean detached checkout:

- Node.js 24.19: **5/5** native tests passed for shared metadata identity,
  public-board labels, unverified social account IDs, deliberately unresolved
  upstream URLs and copyright preservation.
- Python 3: **2/2** existing tests for web manifest naming and root metadata
  import passed.
- `git diff --check` passed; worktree remained clean.

Full React Router build, browser screenshots, asset licensing, SEO rendering,
social-card preview and public deployment remain unverified. Accessibility
improvements are advisory for the founder's hobby-project release criteria;
security/privacy/licensing and actual functional checks remain independent.

## Next acceptance

1. Verify an approved product website and canonical public origin.
2. Replace inherited images only with verified original/rights-cleared assets.
3. Confirm root, public-board, PWA and social metadata in a rendered isolated
   browser build; ensure no fallbacks navigate to Plane's hosted service.
4. Validate actual source/build compatibility in the combined open PR stack
   before merging, and then update canonical Drive records based on results.
