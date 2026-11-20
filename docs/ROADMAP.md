# GoreeCloud Projects — release acceptance plan

## Preview foundation — source-level

Acceptance:
- [x] New public owner repository and original API, web and native client source.
- [x] FastAPI storage/auth and multi-step endpoint tests authored.
- [x] React UI with board/list, status updates, comments and cycles authored.
- [x] GPLv3-only LICENSE and principal dependency notices prepared.
- [x] Native Linux source passed Rust compilation on the authorized development laptop.
- [ ] Linux package, screenshot and native runtime verification.
- [x] Android debug APK assembled on the authorized development laptop.
- [ ] Android UI/device test and signed release.
- [ ] Build provenance, SBOM and full third-party license inventory.
- [ ] GitHub protection and CI verified.
- [ ] UX accessibility/keyboard/full viewport and error/loading acceptance.

## Secure single-user beta

- [ ] Use a real authentication boundary (GoreeCloud Identity), per-project authorization and token rotation.
- [ ] Tested HTTPS-only deployment, CSRF/origin controls as appropriate for auth design, reverse proxy and ingress hardening.
- [ ] Versioned migrations and live SQLite backup+restore rehearsal with integrity checks.
- [ ] Search performance, pagination, audit events, log scrubbing, rate limits and concurrency/load tests.
- [ ] Secure file handling, quotas and attachment scanning only when attachments are introduced.
- [ ] GoreeShield privacy contract and Wardveil threat-model controls verified.
- [ ] Native Linux app packaging lifecycle and Android device lifecycle tested.

## Collaboration milestone (requires a security redesign)

- [ ] Multi-user membership, roles, organization boundaries, invitations and recovery.
- [ ] Audit-grade comments, activity and verified authorship.
- [ ] Epics/modules, milestones, issue dependency links and roadmaps.
- [ ] Mesh integration contracts and explicit consent boundaries.
- [ ] Notifications, external repository references and optional service connectors.

## Operational readiness

- [ ] Automated deploy/rollback, compatibility and disaster recovery drills.
- [ ] Mobile signed release/APK publication after testing.
- [ ] End-to-end browser, Linux and Android acceptance on representative environments.
- [ ] Reconcile authorized documentation and task registry with verified release state.
