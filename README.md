# GoreeCloud Projects

A modern, open-source, **development-stage** project and issue management workspace for self-hosters. Designed as an original, standalone alternative informed by Linear's issue workflows and Plane's self-hosting experience.

> **Status: 0.1.0 development preview. Not production-ready.** This repository contains a tested single-user API and web application, plus native Linux and Android source. Desktop/mobile runtime, credentials, multi-user security, synchronization, upgrades and release acceptance must be independently verified. No stable releases, deployments or signed Android APK are claimed.

## Current implementation

| Component | Technology | Implemented source | Evidence required before release |
| --- | --- | --- | --- |
| API | FastAPI, Pydantic, SQLite | Token-guarded project, issue, cycle, comment, search, stats endpoints | Operational security assessment, migration and restore drills, integration tests |
| Web | React 19, TypeScript, Vite, Lucide | Responsive Kanban and list, create project/issue/cycle, update status/priority/cycle, comments, status filtering and search | Browser accessibility, E2E and multi-viewport testing |
| Linux | Native Slint 1.14.1, Rust | Project/issue lists and creation, token from environment, worker-thread HTTP | Native compilation succeeded on development laptop; installed package and desktop runtime pending |
| Android | Kotlin Multiplatform + Compose Multiplatform shared UI, Material 3 | Native Compose activity: connect, create/list projects and issues | Gradle debug APK built on development laptop; signed app and device lifecycle pending |
| Self-hosting | Python slim image, Compose | Nonroot API Containerfile; loopback-bound Compose deployment recipe | Real deployment, backup/restore, reverse proxy TLS |

There is **no account management, role-based authorization, workspace membership, file upload, realtime sync, webhook delivery, notifications, timeline, Gantt chart, dependency graph, offline writes, import/export, or automation yet**. No browser session cookie or token persistence exists. The API uses a **single high-entropy shared administrator bearer token**; it is inappropriate for untrusted multi-user production use. The projects/assignee model does not grant user accounts or access controls.

## Start the API locally (Linux)

Requires Python 3.12+ and a localhost development environment.

~~~sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r apps/api/requirements-dev.txt
export PROJECTS_ADMIN_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export PROJECTS_DB_PATH="./data/projects.sqlite3"
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
~~~

The token remains in your shell process environment; never commit it, send it to an untrusted server or expose it to browser history. Use a password manager or appropriately permissioned local secret file for controlled development. Database files live under ignored `data/` by default. Endpoint documentation is available at http://127.0.0.1:8000/docs locally. The API must not be placed directly on the public Internet. `/healthz` is intentionally public and returns no private data.

## Web application

In a second terminal:

~~~sh
cd apps/web
npm ci
npm run dev
~~~

Open http://127.0.0.1:5173, paste the development API token, and use the workspace. Vite proxies `/api` to the local API on port 8000. Credentials remain in React memory and are discarded on reload or locking the workspace. Production web hosting requires reviewed TLS termination, correct-origin restrictions and an actual authentication architecture.

Build and check:

~~~sh
cd apps/web && npm ci && npm run build
cd ../..
.venv/bin/python -m pytest -q tests
~~~

## Native Linux client

Requires a Rust 1.88+ toolchain and the native Slint runtime system dependencies (Wayland/X11, OpenGL libraries, C compiler). Slint is a native UI framework approved for GoreeCloud Linux applications—this is not a web wrapper.

~~~sh
export PROJECTS_ADMIN_TOKEN="your-development-token"
export GOREECLOUD_PROJECTS_API_URL="http://127.0.0.1:8000"
cd apps/linux
cargo run
~~~

Keep `PROJECTS_ADMIN_TOKEN` out of shell history. The client rejects remote plain HTTP and credential-bearing URLs; HTTPS or local loopback HTTP is permitted. It does not perform unattended background activity. No Linux package/signature or automatic updater exists.

## Native Android client

Open `apps/android` in Android Studio or build with a compatible Gradle 9.x and Android SDK 37.1/AGP 9.2.0. The app uses Kotlin Multiplatform shared UI and Android Material 3 host UI with initial alpha GoreeCloud UI semantic palette. Production builds require HTTPS. Debug builds allow emulator-loopback HTTP only from the app's network client logic. The token is kept in process memory.

A future hardened integration should use the separately versioned `GoreeCloud/gc-ui` Compose Multiplatform and Material 3 Expressive source adapters after dependency and API compatibility checks. The current app does **not** claim a compiled GC UI adapter dependency, full Material 3 Expressive adoption, or completed device acceptance. A local unsigned-for-release debug APK was built for development; it is not an accepted signed release or physical-device validation.

## Container deployment (local preview only)

Builds are provided in `deploy/Containerfile` and `deploy/compose.yaml`. From the `deploy` folder, provide a random token as an environment variable and run your chosen Compose-compatible engine. The service is bound to `127.0.0.1:8000` and stores SQLite on a volume. Do not put production data here until recovery, TLS, Identity integration and upgrades are accepted.

~~~sh
export PROJECTS_ADMIN_TOKEN="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
cd deploy
podman compose up --build
~~~

The command requires a correctly installed Compose provider; the deployment recipe has not been tested on a live GoreeCloud Containers instance. Never expose the token in logs or use an example token.

## Architecture and MIPS boundaries

- `apps/api`: current source of API/storage truth. Local SQLite, structured JSON and exception responses. Browser and native clients use explicit HTTP contracts.
- `apps/web`: React browser client only; no backend database access.
- `apps/linux`: first-party native Slint/Rust client, independently deployable when verified.
- `apps/android`: Kotlin Compose Android host with KMP shared UI.
- **GoreeCloud UI**: alpha semantic tokens have been referenced for consistency; central design authority remains [GoreeCloud/gc-ui](https://github.com/GoreeCloud/gc-ui).
- **GoreeCloud Mesh**: API contract supports future service integration; **not integrated**.
- **GoreeCloud Identity**: currently replaced by an **insufficient preview shared token**, not integrated; multi-user authorization is blocked until Identity exists.
- **GoreeShield**: data minimization and no telemetry by default; full privacy policy implementation is **pending**.
- **Wardveil**: secure baseline and security review are **pending**, not a deployed security platform.

See [architecture](docs/ARCHITECTURE.md), [competitive evaluation](docs/RESEARCH.md), and [roadmap](docs/ROADMAP.md). The API OpenAPI schema is generated by FastAPI in development. Schema changes are not automatically backward compatible.

## Privacy, recovery and security

Do not use a shared admin token to serve untrusted users or a public production service. Use localhost or a private authenticated development network, and enforce TLS in any real off-host transport. Enforce full RBAC and resource isolation before adding multi-user access. The current `author` and `assignee` fields are plain strings, **not authenticated identities**. Comments are not audit-grade. Application logs must never contain bearer tokens; routine security audits and dependency reviews are still required.

Back up both the SQLite database and operational secrets through a protected channel. SQLite snapshots should be taken using its online backup API, not by copying a live WAL database blindly. This repo does not yet contain a verified backup/restore tool or migration runner. There is no guaranteed recovery point objective.

## Contribution and license

Original GoreeCloud Projects source is released under **GNU General Public License v3.0 only** (see [LICENSE](LICENSE)). Copyright (c) 2026 GoreeCloud and applicable contributors. Third-party libraries remain independently licensed by their respective owners and are **not** relicensed or copied into our source without permission. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) identifies the principal libraries and upstream URLs. Review fresh license inventory and advisories before distribution.

Pull requests should run available CI and be reviewed. Public GitHub visibility is not evidence of a stable service. Production security, privacy, license compliance, packaging, accessibility and physical-device acceptance are separate release gates.
