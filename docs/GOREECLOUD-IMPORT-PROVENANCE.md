# GoreeCloud Projects — import provenance

- Import date: 2026-11-05.
- Destination: public GoreeCloud/projects, main branch.
- Source: https://github.com/makeplane/plane.
- Selected source branch: preview (upstream default).
- Exact upstream commit: 618d0eb74658329a6f6e92434ac54231422c5b96.
- Import type: tracked source snapshot, not upstream commit history.
- Requested source "main" did not exist; checked preview and master, and selected preview as the default.

## Preserved and modified

- Exact original root README retained at docs/UPSTREAM-README.md.
- Original complete LICENSE.txt retained, copied unchanged to LICENSE.
- COPYRIGHT.txt, headers, inherited package/service identifiers retained.
- New first-party GoreeCloud project README and proposed integration contract.
- Browser metadata and PWA application names changed; upstream logos/icons
  and other runtime Plane labels remain, pending licensed asset review.
- 10 original CI workflows preserved verbatim in docs/upstream-github-workflows
  rather than active .github/workflows; do not enable without security review.

## License, security and acceptance

Upstream states AGPL-3.0-only, copyright Plane Software, Inc. and contributors.
The imported derivative must retain notices and conform to the AGPL. Public
source visibility and an imported repository alone do not grant rights to
Plane trademarks or independently licensed third-party media.

A bounded static scan checked tracked readable files for common private-key
PEM headers and GitHub/OpenAI/AWS token patterns. Two existing example matches
were reviewed: an OpenAI-like placeholder in an AI form and an AWS documentation
sample. No code, installers, package hooks, containers or migrations were run.
This is not a comprehensive secret scan or vulnerability/security audit.

Unverified: dependency integrity, install/build, tests, auth/tenant isolation,
UI correctness, portability, backup/restore, GC UI appearance, trademarks,
deployed service, actual user data and all external integrations.

Reconcile and verify future upstream imports independently. Review every
migration, script, dependency, permission and workflow change before enabling.
