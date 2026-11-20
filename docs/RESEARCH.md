# GoreeCloud Projects — research and source selection

## Product benchmark

**Linear** is a workflow benchmark for a responsive issue-first experience, clear status and priority, project planning, cycles, keyboard-speed operations and roadmap integration. See official [Linear](https://linear.app) website and product documentation.

**Plane** is an open-source/self-hosting benchmark for issues, cycles, project pages, modules, documents and flexibility. See the [Plane repository](https://github.com/makeplane/plane) and [official self-hosting documentation](https://plane.so/self-hosted). Plane's Community Edition uses AGPL-3.0. GoreeCloud Projects has **not imported Plane source**, preserving a small original backend and a clean new architecture while evaluating third-party packages individually.

### Decision matrix

| Option | Assessment | Decision |
| --- | --- | --- |
| Fork all Plane | Fast full feature scope but large source/dependency footprint, AGPL network obligations, complex mobile/desktop paths and upstream lifecycle | Deferred; no copied code |
| Build from scratch without dependencies | Clean code but high security/maintenance cost, slower results | Rejected |
| Original domain code + mature open-source components | Self-hostable with clear provenance, smaller maintainable implementation and separate native clients | Chosen for initial preview |
| Electron/Tauri Linux shell | Shares web rendering but violates the current mandatory Linux native UI rule | Rejected |
| Slint/Rust Linux client | Real native UI and GPLv3-compatible distribution | Selected |
| Kotlin Multiplatform Compose + Material 3 Android | Native app, shared Kotlin UI source and approved Android architecture | Selected |
| React/Vite web, FastAPI and SQLite API | Lightweight full-stack implementation and simpler solo-maintainer workflows | Selected |

## Development scope

**Now in source**: projects, issues, statuses, priorities, project-scoped IDs, comments, cycles, API token gate, per-project statistics, browser board and list, Linux and Android starter clients.

**Next**: replace static bearer key with Identity-backed authentication and authorization, build search/indexing and offline cache, project documents and issues hierarchy, attachments, drag/drop with optimistic rollback, audit streams, event-based Mesh integrations, issue relations and dependency graphs, notifications, GitHub integration, import/export and bulk actions.

**Later**: roadmap/timeline, milestones and initiatives, configurable views, analytics, custom fields, templates, scheduled workflows, mobile push and collaboration presence. Real-time and offline sync require a conflict model and tested migration; do not claim those from React or shared Kotlin code alone.

## Maintenance policy

Pin direct dependencies, keep lockfiles, monitor known advisories in CI, read upstream changelogs before upgrades, and audit all redistribution and transitive licenses. Slint requires special attention to its GPLv3 open-source grant. Honor GCC/Qt/Android licenses, Gradle, container base images, and signing. Verified ecosystem GoreeCloud UI alpha tokens are **candidates, not approved Stable brand colors**.

This is a research record and direction, not proof of feature completeness, runtime verification, a release, or an operating service.
