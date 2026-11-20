# Third-party dependency and attribution register

GoreeCloud Projects contains original first-party application code alongside package-managed dependencies. No source files from Linear or Plane have been copied, forked, or relicensed. The bundled `LICENSE` is the full GNU GPLv3 legal text obtained from the canonical GPL text mirrored by [Slint](https://github.com/slint-ui/slint/blob/master/LICENSES/GPL-3.0-only.txt). Copyright and license notices in upstream packages remain applicable.

| Library or reference | Role | Upstream | License (recheck release metadata) |
| --- | --- | --- | --- |
| FastAPI / Starlette | API and ASGI web framework | https://github.com/fastapi/fastapi , https://github.com/encode/starlette | MIT / BSD-3-Clause |
| Pydantic | Request and response validation | https://github.com/pydantic/pydantic | MIT |
| Uvicorn | ASGI server | https://github.com/encode/uvicorn | BSD-3-Clause |
| SQLite | Embedded durable data store | https://sqlite.org/ | Public domain |
| React / React DOM | Browser user interface | https://github.com/facebook/react | MIT |
| Vite | Browser application bundler | https://github.com/vitejs/vite | MIT |
| TypeScript | Static type checking | https://github.com/microsoft/TypeScript | Apache-2.0 |
| Lucide React | UI icons | https://github.com/lucide-icons/lucide | ISC |
| Slint | Native Linux desktop UI | https://github.com/slint-ui/slint | GPL-3.0-only open-source option / alternate commercial grants |
| ureq | Rust HTTP requests | https://github.com/algesten/ureq | MIT / Apache-2.0 |
| Serde / serde_json | Rust serialization | https://github.com/serde-rs/serde | MIT / Apache-2.0 |
| Kotlin, Compose Multiplatform | Shared Kotlin UI | https://github.com/JetBrains/kotlin , https://github.com/JetBrains/compose-multiplatform | Apache-2.0 |
| Jetpack Compose / Material 3 | Native Android UI | https://developer.android.com/jetpack/compose | Apache-2.0 |
| Gradle / Android Gradle Plugin | Android build tooling | https://gradle.org/ , https://developer.android.com/build | Apache-2.0 |

Dependencies may have additional transitives, assets and separate terms. Package locks do **not** substitute for a full transitive license report. Validate production artifacts, distributed notices and version-specific conditions prior to release.

Other researched products (not embedded as source): [Linear](https://linear.app), [Plane](https://github.com/makeplane/plane). Plane's open-source Community Edition is AGPL-3.0; this is **not a fork**.
