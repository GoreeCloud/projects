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

## Unverified and deployment gates

- No application dependencies were installed, built, loaded or executed by this audit. Runtime and test compatibility of the updated graph is **not yet accepted**.
- Review any changed dependency licenses and actual artifacts before installation; registry resolution and integrity fields alone do not guarantee safety.
- Verify behavior of Axios redirects, React Router/Express integration, Vitest test suites, and backend security in an isolated environment.
- The Python `apps/api/uv.lock` dependency graph was not covered by pnpm audit.
- GitHub Dependabot alerts returned **disabled** for the repository; enabling security features requires appropriate authorization/settings access.
- Maintain the inherited Plane AGPL-3.0-only license and third-party notices.
- Do not deploy, publish a release, or label the imported application security-cleared based only on this result.

Related tracking: [GitHub issue #4](https://github.com/GoreeCloud/projects/issues/4).
