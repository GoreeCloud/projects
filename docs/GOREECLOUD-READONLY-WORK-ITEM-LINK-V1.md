# GoreeCloud Projects — read-only work-item reference v1

**Status:** proposed development contract; no live cross-product integration, no
shared login, no task synchronization and no deployment.
**Source authority:** `GoreeCloud/projects`; existing Teams and Tasks repositories
must be verified independently before implementation.
**Scope:** future permission-checked reference from a Workspace Teams message
to a Plane-derived Projects work item. **Not a shared task record.**

## Contract

Files:

- `contracts/work-item-reference.v1.schema.json` — proposed versioned
  JSON Schema (2020-12) and allowed field names.
- `contracts/work-item-reference.v1.mjs` — dependency-free strict parser,
  canonical serializer, and frozen normalized locator.
- `tests/test_work_item_reference_contract.mjs` — isolated input-hardening tests.

Example with **synthetic IDs**, not real GoreeCloud tenant data:

```json
{
  "schema_version": 1,
  "source": "goreecloud-projects",
  "entity_type": "work_item",
  "workspace_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "project_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "work_item_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
}
```

The schema contains **only a locator**, with no title, description, member
details, token, arbitrary URL, browser origin, or cached project summary.
Validation accepts only canonical lower-case hyphenated UUIDs, exact source/type
values, and a fixed major schema version; extra fields fail closed. JSON input
is capped at 1024 bytes. The parser returns a fresh immutable object, never
the untrusted input object.

A reference is **not an authorization grant**. An ID can still reveal that an
object might exist, so source-object IDs must not be pasted into a Teams space
without checking the intended audience. The schema itself cannot enforce
access control, tenant isolation, or membership revocation.

## Required permission chain before any real link can be resolved

1. **At creation:** a future authenticated Teams action must verify the
   writer is allowed to post in the destination message/channel and has access
   to the referenced Projects workspace/project/work item, using a trusted
   common identity mapping or a server-side delegated capability that does not
   leak into the saved locator.
2. **At storage:** Teams must store the envelope only inside its existing
   membership-scoped space/channel records. Do not create an index publicly
   searchable by foreign users; do not save credentials or work-item details.
3. **At read:** Teams must re-check the viewer's membership, and an authorized
   Projects resolver must separately re-check that viewer's **current**
   tenant/project/work-item rights. A previously valid link is not sufficient.
4. **At display:** authorized viewers may receive only the minimum fields
   required to render the link; unauthorized, deleted, revoked, missing or
   unavailable references display a neutral placeholder, without leaking
   existence or differing user details.
5. **At navigation:** build URLs exclusively from a configured trusted Projects
   origin and validated IDs after authorization. Never trust a user-supplied
   URL or infer access from a signed-in Teams session. Do not forward login
   cookies, authorization headers or service secrets through the reference.
6. **At removal:** when membership is revoked, old message previews and caches
   must be invalidated; repeat fetches must fail. Audit only authorized
   actions without printing secrets or private content.

These are **release gates**, not implemented behavior. Workspace Teams
currently runs a limited local web/API alpha with separate identities;
GoreeCloud Tasks clients remain device-local without a shared canonical
server. Therefore the proposed reference parser must stay disconnected from
any live resolver, public index, message renderer or synchronization job until
a verified identity and authorization architecture exists.

## Explicitly prohibited v1 behavior

- No remote endpoint calls, webhooks, message writes, task creation, state
  changes, automatic previews or task synchronization from this parser.
- No two-way dual writes, direct Teams/Projects database queries or automatic
  creation of a GoreeCloud Tasks record from a Plane issue.
- No reusing the reference as a bearer token or cross-system identity proof.
- No unbounded JSON payloads, user-supplied URL destinations, executable
  metadata or arbitrary fields.

## Validation performed

```sh
node --test tests/test_work_item_reference_contract.mjs
```

**9/9 isolated Node.js tests passed** on November 5, 2026 in a clean
detached checkout: schema/implementation shape, normalization, immutability,
strict fields/version/type/UUID checks, accessor rejection, prototype pollution
rejection, bounded malformed JSON and deterministic serialization.
No third-party packages, network calls, Teams/Tasks accounts or production
services were involved.

## Next gates

- Confirm actual user-account federation and owner-controlled service origins.
- Test link creation, reading, navigation, deletion, revocation and audit
  events across both products with synthetic users in an isolated environment.
- Define an explicit source capability to fetch **one authorized work item**
  with tenant scoping, rate limits and no cross-tenant list capability.
- Review retention and export behavior: Teams space JSON exports currently
  include space content, and links must not become hidden credentials.
- Only after a server-backed GoreeCloud Tasks API and canonical identity model
  exists, define separate mapping, event, idempotency, conflict and rollback
  contracts for optional task synchronization.

This document is a design/tested-parser artifact, **not an integration
deployment acceptance**. Governed Drive records remain the documentation
authority for approved project status.
