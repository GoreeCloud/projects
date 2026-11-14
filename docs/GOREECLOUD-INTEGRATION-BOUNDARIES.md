# GoreeCloud Projects — proposed integration boundaries

**[GoreeCloud OpenRoom](https://github.com/GoreeCloud/openroom)** (formerly GoreeCloud Workspace Teams): communication, channels, membership, linked project
discussions and collaboration notifications. Not a parallel developer issue registry.

**Projects:** issues/work items, cycles, modules, milestones, roadmaps,
release readiness, dependencies and project documentation. Imported Plane work
items currently belong to Plane's own database; no cross-product sync exists.

**Tasks:** proposed canonical cross-product task identity/assignment/priority/
status/scheduling record after a versioned API, authorization and migration exist.
Do not claim the currently device-local Tasks clients are an active shared service.

## Safe staged integration

1. Link issue URLs/IDs in authorized OpenRoom conversations without copying records.
2. Use authenticated, permission-filtered, versioned events and idempotency keys.
3. Verify shared identity, project roles, membership revocation and private links.
4. Introduce explicit Plane-ID to GoreeCloud Task-ID mapping with field authority,
   conflict handling, tombstones, audit history, recovery tests and rollback.
5. Enable approved mutations only after reliable one-way read projection and
   controlled migration; avoid two-way dual-write loops or direct database access.
6. Let GoreeCloud Manager consume read-only health summaries, and Notify send
   user-opted-in alerts. AI proposes changes with scoped approvals before writing.

## Planned enhancements

GitHub commit/PR/CI associations, bug/feature intake, cross-repository
dependencies, release checklists, evidence-based status reporting, and opt-in
GoreeCloud AI planning/triage. None is implemented by this source import.
