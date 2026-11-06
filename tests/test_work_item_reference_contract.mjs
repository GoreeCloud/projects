// Copyright (c) 2026 GoreeCloud
// SPDX-License-Identifier: AGPL-3.0-only
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  WORK_ITEM_REFERENCE_VERSION,
  normalizeWorkItemReference,
  parseWorkItemReferenceJson,
  serializeWorkItemReference,
} from "../contracts/work-item-reference.v1.mjs";

const VALID = Object.freeze({
  schema_version: 1,
  source: "goreecloud-projects",
  entity_type: "work_item",
  workspace_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  project_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  work_item_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
});

const schema = JSON.parse(readFileSync(
  new URL("../contracts/work-item-reference.v1.schema.json", import.meta.url), "utf8",
));

test("schema version, fields and UUID restrictions agree with implementation", () => {
  assert.equal(WORK_ITEM_REFERENCE_VERSION, schema.properties.schema_version.const);
  assert.equal(schema.properties.source.const, VALID.source);
  assert.equal(schema.properties.entity_type.const, VALID.entity_type);
  assert.equal(schema.additionalProperties, false);
  assert.deepEqual(
    schema.required.slice().sort(),
    Object.keys(VALID).sort(),
  );
  const uuid = new RegExp(schema.$defs.uuid.pattern);
  for (const key of ["workspace_id", "project_id", "work_item_id"]) {
    assert.match(VALID[key], uuid);
    assert.equal(schema.properties[key].$ref, "#/$defs/uuid");
  }
});

test("accepts canonical opaque IDs and returns a fresh immutable locator", () => {
  const normalized = normalizeWorkItemReference(VALID);
  assert.deepEqual(normalized, VALID);
  assert.notStrictEqual(normalized, VALID);
  assert.equal(Object.isFrozen(normalized), true);
});

test("never accepts titles, URLs, auth tokens, user details or extra data", () => {
  for (const field of ["title", "url", "token", "email", "display_name", "task_status"]) {
    assert.throws(() => normalizeWorkItemReference({ ...VALID, [field]: "sensitive" }), TypeError);
  }
  assert.throws(() => normalizeWorkItemReference({
    ...VALID, entity_type: "work_item", __proto__unused: true,
  }), TypeError);
});

test("rejects missing fields, wrong types, unsupported versions and kinds", () => {
  for (const field of Object.keys(VALID)) {
    const incomplete = { ...VALID };
    delete incomplete[field];
    assert.throws(() => normalizeWorkItemReference(incomplete), TypeError);
  }
  for (const input of [
    null, [], "anything", 5,
    { ...VALID, schema_version: 2 },
    { ...VALID, schema_version: "1" },
    { ...VALID, source: "goreecloud-tasks" },
    { ...VALID, entity_type: "project" },
  ]) assert.throws(() => normalizeWorkItemReference(input), TypeError);
});

test("rejects upper-case, invalid and non-string UUIDs without normalizing identities", () => {
  for (const key of ["workspace_id", "project_id", "work_item_id"]) {
    for (const invalid of [VALID[key].toUpperCase(), "not-a-uuid", 1, "", null, "a".repeat(36)]) {
      assert.throws(() => normalizeWorkItemReference({ ...VALID, [key]: invalid }), TypeError);
    }
  }
});

test("does not invoke attacker-controlled accessors or accept exotic prototypes", () => {
  let called = false;
  const tainted = { ...VALID };
  Object.defineProperty(tainted, "project_id", {
    enumerable: true,
    get() { called = true; throw new Error("Getter must never run"); },
  });
  assert.throws(() => normalizeWorkItemReference(tainted), TypeError);
  assert.equal(called, false);
  assert.throws(() => normalizeWorkItemReference(new Date()), TypeError);
});

test("rejects prototype pollution payloads in untrusted JSON", () => {
  const text = JSON.stringify(VALID).replace(
    /}\s*$/, ', "__proto__":{"admin":true}}',
  );
  assert.throws(() => parseWorkItemReferenceJson(text), TypeError);
  assert.equal({}.admin, undefined);
});

test("parses bounded JSON and rejects oversized or malformed payloads", () => {
  assert.deepEqual(parseWorkItemReferenceJson(JSON.stringify(VALID)), VALID);
  assert.throws(() => parseWorkItemReferenceJson("x"), SyntaxError);
  assert.throws(() => parseWorkItemReferenceJson("x".repeat(1025)), TypeError);
  assert.throws(() => parseWorkItemReferenceJson(JSON.stringify({ ...VALID, title: "x".repeat(900) })), TypeError);
});

test("serialized output is deterministic and contains no display or access data", () => {
  const swapped = Object.fromEntries(Object.entries(VALID).reverse());
  const canonical = serializeWorkItemReference(swapped);
  assert.equal(canonical, serializeWorkItemReference(VALID));
  assert.deepEqual(JSON.parse(canonical), VALID);
  assert.ok(!canonical.includes("http"));
  assert.equal(parseWorkItemReferenceJson(canonical).work_item_id, VALID.work_item_id);
});
