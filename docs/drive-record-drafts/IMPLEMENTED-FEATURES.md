# GoreeCloud Projects — Implemented Features (Draft)

**Record type:** Source-backed implementation inventory.
**Prepared:** November 5, 2026.
**Status:** NONCANONICAL GITHUB REVIEW DRAFT — not yet uploaded to the canonical Drive Markdown file.
**Intended authoritative destination:** `GoreeCloud/Projects/GoreeCloud Projects/IMPLEMENTED-FEATURES.md`.
**Source repository:** https://github.com/GoreeCloud/projects

## Verified source and repository capabilities

| Capability | What is evidenced | Acceptance level |
| --- | --- | --- |
| Imported project execution foundation | The tracked upstream Plane `preview` source snapshot is in `main` at `209ac94af92671d49dee16e1aa3a7c288f47029a`; root `README.md` documents import and scope. | Source imported; application not commissioned or deployed |
| Multi-service code structure | Imported `apps/web`, `apps/api`, `apps/admin`, `apps/space`, `apps/live` and shared packages. | Source present; end-to-end interoperability untested |
| Project/work item/cycle/module foundation | Plane-derived models, UI and backend source for work items, cycles, project modules, and planning are in the import. | Code capability inherited; GoreeCloud acceptance pending |
| Repository licensing and attribution | `LICENSE` and `LICENSE.txt` retain AGPL-3.0-only license text; `COPYRIGHT.txt` and upstream source notices preserved. | File and provenance review complete; third-party brand and media rights still require review |
| Import provenance and integration boundaries | `docs/GOREECLOUD-IMPORT-PROVENANCE.md` and `docs/GOREECLOUD-INTEGRATION-BOUNDARIES.md` record origin and planned product boundaries. | Documentation in repository |
| Initial product identity | Repository name and selected browser/PWA metadata identify GoreeCloud Projects. | Partial rebrand only; inherited Plane assets, links and constants remain |
| CI safety boundary | Ten upstream GitHub workflow files are archived under `docs/upstream-github-workflows/` rather than active workflow paths. | No imported CI active; secure CI not yet commissioned |
| Initial focused regression coverage | Draft pull requests contain telemetry, Python dependency, JavaScript dependency, and web metadata checks. | Tests verified on isolated branches, **not merged in `main`** |

## Confirmed gaps and exclusions

- **No verified production deployment**, hosted URL, live account migration, full Docker/Kubernetes acceptance or complete end-to-end test suite.
- **No deployed Teams or Tasks integration.** The imported Plane project database is not a unified GoreeCloud Tasks server; Workspace Teams retains independent alpha task records.
- **No verified shared identity**, SSO, multi-tenant authorization certification, network privacy certification or backup/restore drill.
- **No complete GoreeCloud UI compliance** or rights-cleared replacement of all inherited Plane branding.
- Draft work is not implemented on `main`: [telemetry PR #3](https://github.com/GoreeCloud/projects/pull/3), [JavaScript dependency PR #5](https://github.com/GoreeCloud/projects/pull/5), [PWA metadata PR #7](https://github.com/GoreeCloud/projects/pull/7), [OpenTelemetry PR #8](https://github.com/GoreeCloud/projects/pull/8).
- Dependency-advisory counts reflect scan dates and proposed lockfiles; they do not establish runtime exploitability or production safety.

## Verification and source hierarchy

GitHub owns code and live PR state; canonical GoreeCloud Drive owns accepted project documentation. This is a review draft only. Revalidate heads, license, tests and deployment status before moving this text into the authoritative Drive record.
