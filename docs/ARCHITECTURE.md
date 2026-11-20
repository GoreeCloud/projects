# GoreeCloud Projects — initial architecture

## Current, verified-source architecture

Development preview with one local administrator token and no hosted service.

```text
Web (React/Vite) --------+
Linux (Slint/Rust) ------+-- bearer token -> FastAPI /api/v1 --> SQLite
Android (KMP Compose) ---+                    |
                                              +--> projects
                                              +--> cycles
                                              +--> issues
                                              +--> comments
```

The API owns project keys and sequential issue numbering. SQLite `BEGIN IMMEDIATE` reserves a unique number when creating issues. Native app clients do not have direct database access. Project operations have no nested workspace identity or RBAC: a valid token grants access to all records. This makes the present system suitable for private development, **not untrusted team collaboration**.

### API contracts

- `GET /healthz` is public and intentionally generic.
- `GET|POST /api/v1/projects`: list and create.
- `GET|PATCH /api/v1/projects/{project_id}`: read, edit metadata or archive.
- `GET|POST /api/v1/projects/{project_id}/issues`: list with capped pagination, literal search and optional status; create an issue with atomic project-scoped number.
- `GET|PATCH /api/v1/issues/{issue_id}`: read/update status, priority, assignee text, title, description, cycle and due date.
- `GET|POST /api/v1/projects/{project_id}/cycles`: list/create cycles and validate date windows.
- `GET|POST /api/v1/issues/{issue_id}/comments`: list/create comments (author is unverified text).
- `GET /api/v1/projects/{project_id}/stats`: issue counts by status.

All private endpoints require `Authorization: Bearer ...`. No write requests are accepted without the token. All storage access uses parameterized SQLite queries; caller-controlled enum values are Pydantic constrained, and dynamic SQL update column names originate only from strongly validated Pydantic field names, not arbitrary request keys.

### Trust boundaries and risks

- **Shared root key**: no user identity, project ACL, per-role authorization, account recovery or token rotation mechanism. Replace with GoreeCloud Identity + project-scoped RBAC before production.
- **HTTPS**: API deployment is intended for loopback. Configure trusted reverse proxy/TLS before off-host clients; Android production builds reject HTTP, Linux rejects non-loopback HTTP, and the web client still requires trustworthy HTTPS hosting and an operator-controlled API origin.
- **Privacy**: no built-in tracking or telemetry. Contacts/assignees are unverified arbitrary text. GoreeShield policy enforcement is a planned integration, not implemented.
- **Security**: rate limiting, structured audit, threat detection, secret rotation, resource quotas and integration with Wardveil are pending. Token validation is constant time.
- **Integration**: Mesh event schemas and webhook signature validation are future contracts, not actual runtime integration.
- **Availability**: no HA or distributed database; SQLite on one host with backup and recovery required.
- **Data integrity**: initial schema has user_version=1 but no migration runner; snapshot and migration verification are prerequisites to upgrades.
- **Releases**: Android device testing/signing and Linux installer/desktop runtime acceptance are pending unless separately evidenced in build logs.

### Dependency choices

FastAPI/Pydantic provide typed, documented HTTP and strong validation while keeping the service small. SQLite enables low-overhead self-hosting; when concurrent users, migrations, or search justify it, a deliberate PostgreSQL backend can be introduced. React enables a fast browser client and is among the permitted GoreeCloud web stacks. Slint is a valid native Linux UI per governing rules, not a web view. Kotlin Multiplatform + Compose shares Android UI code and keeps Material 3 as the Android host. GoreeCloud UI remains the sole design authority.

### Future compatibility

Maintain API version prefix and publish schema version per release. Use additive migrations and compatibility adapters; do not silently rewrite users' data. Integrations with GoreeCloud Tasks (personal todos), Notebook (documentation), Teams (discussion), Mesh (events), Identity, Notify (notifications), GoreeShield and Wardveil require explicit contracts, consent and authorization gates—not automatic cross-product data exchange.
