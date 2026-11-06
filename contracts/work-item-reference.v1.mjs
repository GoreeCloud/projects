// Copyright (c) 2026 GoreeCloud
// SPDX-License-Identifier: AGPL-3.0-only
//
// Standalone, dependency-free reference validation. NOT a live integration,
// identity provider, authorization mechanism, or cross-product task sync.

export const WORK_ITEM_REFERENCE_VERSION = 1;
export const WORK_ITEM_REFERENCE_SOURCE = "goreecloud-projects";
export const WORK_ITEM_REFERENCE_ENTITY = "work_item";

const ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const FIELDS = Object.freeze([
  "schema_version",
  "source",
  "entity_type",
  "workspace_id",
  "project_id",
  "work_item_id",
]);

function assertRawRecord(input) {
  if (input === null || typeof input !== "object" || Array.isArray(input)) {
    throw new TypeError("A work-item reference must be a plain JSON object");
  }

  const proto = Object.getPrototypeOf(input);
  if (proto !== Object.prototype && proto !== null) {
    throw new TypeError("A work-item reference must be a plain JSON object");
  }

  const actualKeys = Reflect.ownKeys(input);
  if (actualKeys.length !== FIELDS.length || actualKeys.some((key) => !FIELDS.includes(key))) {
    throw new TypeError("Unexpected or missing work-item reference field");
  }

  // Reject accessors rather than triggering untrusted getters while validating.
  const descriptors = Object.getOwnPropertyDescriptors(input);
  for (const key of FIELDS) {
    if (!Object.hasOwn(descriptors, key) || !Object.hasOwn(descriptors[key], "value")) {
      throw new TypeError("Work-item reference fields must be plain values");
    }
  }

  return descriptors;
}

export function normalizeWorkItemReference(input) {
  const fields = assertRawRecord(input);
  const value = (key) => fields[key].value;

  if (value("schema_version") !== WORK_ITEM_REFERENCE_VERSION ||
      value("source") !== WORK_ITEM_REFERENCE_SOURCE ||
      value("entity_type") !== WORK_ITEM_REFERENCE_ENTITY) {
    throw new TypeError("Unsupported work-item reference version or kind");
  }
  for (const key of ["workspace_id", "project_id", "work_item_id"]) {
    if (typeof value(key) !== "string" || !ID_PATTERN.test(value(key))) {
      throw new TypeError("Invalid canonical work-item reference ID: " + key);
    }
  }

  // Construct a fresh, immutable, strictly allowlisted locator. It never
  // includes private work-item titles, messages, user details, or URLs.
  return Object.freeze({
    schema_version: WORK_ITEM_REFERENCE_VERSION,
    source: WORK_ITEM_REFERENCE_SOURCE,
    entity_type: WORK_ITEM_REFERENCE_ENTITY,
    workspace_id: value("workspace_id"),
    project_id: value("project_id"),
    work_item_id: value("work_item_id"),
  });
}

export function parseWorkItemReferenceJson(json) {
  if (typeof json !== "string" || new TextEncoder().encode(json).length > 1024) {
    throw new TypeError("Work-item reference JSON must be a string of at most 1024 bytes");
  }
  return normalizeWorkItemReference(JSON.parse(json));
}

export function serializeWorkItemReference(input) {
  return JSON.stringify(normalizeWorkItemReference(input));
}
