# GoreeCloud Projects — dependency audit and patch verification

**Date:** 2026-11-05. **Scope:** JavaScript pnpm workspace lockfile imported from Plane preview; development-only.

## Verified baseline

A read-only `pnpm audit --json` on the original `main` lockfile reported **9 advisories**: 1 high, 6 moderate, 2 low, across 1,411 reported dependency entries. This count is of advisories, not nine separately exploitable packages or verified vulnerabilities in the GoreeCloud runtime.

The high-severity advisory was `follow-redirects` 1.16.1 (`GHSA-mrwp-f3q8-3g9p`), a transitive dependency of Axios in multiple workspace packages.

## Minimal patch set

- `follow-redirects`: 1.16.1 to 1.16.2.
- `fast-uri`: 3.1.8 to 3.1.9.
- `qs`: 6.16.0 to 6.16.1.
- `vitest` and `@vitest/coverage-v8`: 4.1.11 to 4.1.12 through catalog floor updates, bringing `@vitest/mocker` to 4.1.12.

Only `pnpm-workspace.yaml` and its generated `pnpm-lock.yaml` were changed for dependency resolution. Existing overrides for other components remain intact. The lockfile was regenerated with `pnpm install --lockfile-only --ignore-scripts --frozen-lockfile=false --prefer-offline`, without installing application dependencies or running package lifecycle scripts.

## Post-patch result

A second read-only `pnpm audit --json` reported **1 moderate advisory, 0 high, 0 critical, 0 low**, down from 9 total. The remaining finding is `minimatch` 10.2.3, `GHSA-g3hv-75wg-m249`, which reports a patched range beginning at 11.0.1. The existing `minimatch@10` exact override is retained until the major-version compatibility of developer tooling is validated. It has **not** been suppressed.

## Unmerged minimatch v11 compatibility preflight (November 5, 2026)

The existing `minimatch@10: 10.2.3` override and **this PR's lockfile remain unchanged**.
The project's current import has no direct `minimatch` source imports in a
bounded tracked-source scan; the staged 11.0.1 lockfile candidate resolves
three transitive consumers: `@eslint/config-array@0.23.5`, `eslint@10.4.1`,
and `deslop-js@0.0.21`. This does not prove that all developer tooling is
compatible across a major version.

Read-only review of a **previously created isolated candidate** found that
replacing the `minimatch@10` override with `11.0.1` changes the generated
lockfile's `minimatch` entry and introduces `@isaacs/nonrecursive-glob-match@1.0.3`.
The saved candidate audit artifact reports **zero advisories**, but this is
**not** a fresh audit of the checked-in PR or a verified install/build.
Review the new package's license/notice obligations separately.

In an existing installation fixture (no fresh installation), under Node
24's `--permission` mode with only fixture-directory read access and no
network permissions:

- The actual `minimatch@11.0.1` named exports and **five ordinary** glob
  patterns passed bounded smoke checks.
- An isolated `ESLint@10.4.1` test using ordinary `**/*.js` config matching
  returned zero errors for a valid source string and exactly one for an invalid
  one. This exercises one consumer, **not** a complete project lint run.
- The attempt to import the `deslop-js` consumer while restricting native
  addons stopped at its unrelated `oxc-parser` native binding with
  `ERR_DLOPEN_DISABLED`. Do not relax this sandbox limit solely to claim a
  passing compatibility test. That consumer and the full project remain
  **untested**.
- Upstream minimatch v11 removes `Minimatch.makeRe()`, the `regexp`
  property, and several implementation methods. A bounded source scan of
  these three transitive consumers found references to the exported
  `Minimatch` class or `minimatch()` function, not those removed APIs.
  This is static evidence, not a blanket compatibility guarantee.

**Corepack working-directory finding (resolved for this repository):**
The initial `pnpm --version` command ran from Desktop Commander's
**default working directory outside the Projects repository** and failed
because Corepack selected an unavailable cached 11.28.6 entry. Follow-up
read-only verification explicitly changed to the GoreeCloud Projects root,
where its `packageManager` pin correctly selected **pnpm 11.10.0** and the
command succeeded. The current Projects source checkout remained clean.
The unrelated default-directory Corepack cache remains unchanged; **do not
treat it as a blocker for running the project-pinned package manager**.
No global shim was repaired or replaced.

**Decision:** Keep this PR at the existing verified **one moderate finding**.
Do not assert that the `minimatch` advisory is remediated in the repository.
Remaining gates are the resolved-graph license review, offline-compatible
package-manager integrity, `deslop-js` functionality, full source/build/test
validation, and fresh audit of the exact candidate before separately
approving the major version change.

## Unverified and deployment gates

- No application dependencies were installed, built, loaded or executed by this audit. Runtime and test compatibility of the updated graph is **not yet accepted**.
- Review any changed dependency licenses and actual artifacts before installation; registry resolution and integrity fields alone do not guarantee safety.
- Verify behavior of Axios redirects, React Router/Express integration, Vitest test suites, and backend security in an isolated environment.
- The Python `apps/api/uv.lock` dependency graph was not covered by pnpm audit.
- GitHub Dependabot alerts returned **disabled** for the repository; enabling security features requires appropriate authorization/settings access.
- Maintain the inherited Plane AGPL-3.0-only license and third-party notices.
- Do not deploy, publish a release, or label the imported application security-cleared based only on this result.

Related tracking: [GitHub issue #4](https://github.com/GoreeCloud/projects/issues/4).
