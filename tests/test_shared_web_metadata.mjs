// Copyright (c) 2026 GoreeCloud
// SPDX-License-Identifier: AGPL-3.0-only
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  SITE_NAME,
  SITE_TITLE,
  SITE_DESCRIPTION,
  SPACE_SITE_NAME,
  SPACE_SITE_TITLE,
  SPACE_SITE_DESCRIPTION,
  TWITTER_USER_NAME,
  SPACE_TWITTER_USER_NAME,
  SITE_URL,
  SPACE_SITE_URL,
} from "../packages/constants/src/metadata.ts";

test("shared primary metadata uses GoreeCloud Projects identity", () => {
  assert.equal(SITE_NAME, "GoreeCloud Projects");
  assert.equal(SITE_TITLE, "GoreeCloud Projects | Project planning and delivery");
  assert.match(SITE_DESCRIPTION, /GoreeCloud Projects/);
  for (const text of [SITE_NAME, SITE_TITLE, SITE_DESCRIPTION]) {
    assert.doesNotMatch(text, /\bPlane\b/i);
  }
});

test("public-board metadata uses GoreeCloud Projects and has no typo", () => {
  assert.equal(SPACE_SITE_NAME, "GoreeCloud Projects Public Boards");
  assert.equal(SPACE_SITE_TITLE, "GoreeCloud Projects | Public boards");
  assert.match(SPACE_SITE_DESCRIPTION, /GoreeCloud Projects/);
  for (const text of [SPACE_SITE_NAME, SPACE_SITE_TITLE, SPACE_SITE_DESCRIPTION]) {
    assert.doesNotMatch(text, /\bPlane\b|pubic/i);
  }
});

test("does not claim ownership of an unverified social account", () => {
  assert.equal(TWITTER_USER_NAME, "");
  assert.equal(SPACE_TWITTER_USER_NAME, "");
});

test("keeps upstream URLs visible as separate unresolved release blockers", () => {
  // These exports are intentionally NOT rewritten to an invented GoreeCloud
  // origin. They are not used by current in-repo consumers, and must be
  // reviewed before a public deploy instead of being adopted silently.
  assert.equal(SITE_URL, "https://app.plane.so/");
  assert.equal(SPACE_SITE_URL, "https://app.plane.so/");
});

test("preserves upstream copyright and license attribution", () => {
  const source = readFileSync(
    new URL("../packages/constants/src/metadata.ts", import.meta.url), "utf8",
  );
  assert.match(source, /Copyright \(c\) 2023-present Plane Software, Inc. and contributors/);
  assert.match(source, /SPDX-License-Identifier: AGPL-3\.0-only/);
});
