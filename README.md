# GoreeCloud Projects

**Rebranded Import** of [Plane](https://github.com/makeplane/plane) for GoreeCloud.

> **Development/source baseline only. Not deployed or production-ready.**
> The GoreeCloud user interface and integrations are not yet complete.
> This is an attributed Plane derivative, not independently authored replacement software.

## Purpose

Project execution and software delivery: work items, issues, cycles, modules,
milestones, project documentation, dependencies, roadmaps, planning and releases.

- **GoreeCloud Workspace Teams:** where people communicate and collaborate.
- **GoreeCloud Projects:** where people organize, build, verify and ship projects.
- **GoreeCloud Tasks:** intended future canonical shared task record across products.

Today this import retains Plane's existing work-item models and separate database.
**There is no live cross-product task sync, shared login, or Teams integration.**
See [integration boundaries](docs/GOREECLOUD-INTEGRATION-BOUNDARIES.md).

## Source and provenance

- Upstream: https://github.com/makeplane/plane
- Upstream branch imported: **preview**, the upstream default on 2026-11-05.
- Upstream commit: [618d0eb74658329a6f6e92434ac54231422c5b96](https://github.com/makeplane/plane/commit/618d0eb74658329a6f6e92434ac54231422c5b96).
- Plane has no main branch; preview is used as the closest current baseline.
- Import method: complete tracked source snapshot with changes documented separately.
- Original README: [docs/UPSTREAM-README.md](docs/UPSTREAM-README.md).
- Detailed provenance: [docs/GOREECLOUD-IMPORT-PROVENANCE.md](docs/GOREECLOUD-IMPORT-PROVENANCE.md).

Internal upstream package names and service identifiers remain intact for compatibility.
The initial rebrand covers repository identity and targeted browser/PWA metadata;
many UI labels, icons, media assets and domain references still use Plane identity.
**Do not describe the runtime as fully rebranded.** GoreeCloud UI adoption is planned.

## License and attribution

This derivative retains upstream **AGPL-3.0-only** terms. The original
[LICENSE.txt](LICENSE.txt) and [COPYRIGHT.txt](COPYRIGHT.txt) are preserved,
with an identical [LICENSE](LICENSE) copy for the GoreeCloud repository policy.
Preserve file headers, third-party notices and contributors' rights.

Upstream source authors: **Plane Software, Inc. and contributors**.
GoreeCloud does not claim authorship of inherited code or ownership of upstream
trademarks, logos or media. The AGPL includes source-sharing conditions for
relevant modified network-served versions. Review third-party rights before release.

## Deployment and security

**Do not deploy the raw import.** Its dependencies, scripts, auth, tenancy,
asset rights, data isolation and recovery have not been independently accepted.
No installation hooks, containers or upstream scripts were executed in importing.

The 10 upstream Actions workflows were relocated outside active workflow paths
to [docs/upstream-github-workflows](docs/upstream-github-workflows), pending review.
No automatic imported workflow is enabled.

## Next implementation milestones

1. Review license/asset rights, dependencies, vulnerabilities and automation.
2. Implement GoreeCloud UI and lawfully replace upstream trademark-bearing assets.
3. Verify builds, secure installation, authorization, test data and recoverability.
4. Build a validated shared Tasks contract and mapped work-item identities.
5. Integrate Workspace Teams for permission-checked conversation links and notices.
6. Add opt-in GitHub links, issue intake, and release evidence without redundant data.
