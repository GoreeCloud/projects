# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Dependency-free checks for web app/PWA naming consistency."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WebMetadataTests(unittest.TestCase):
    def test_public_manifests_use_project_name(self):
        for name in (
            "apps/web/manifest.json",
            "apps/web/public/manifest.json",
            "apps/web/public/site.webmanifest.json",
        ):
            with self.subTest(path=name):
                data = json.loads((ROOT / name).read_text())
                self.assertEqual(data["name"], "GoreeCloud Projects")
                self.assertEqual(data["short_name"], "GC Projects")

    def test_root_metadata_import_is_not_stale(self):
        source = (ROOT / "apps/web/app/root.tsx").read_text()
        self.assertIn('import { SITE_DESCRIPTION } from "@plane/constants";', source)
        self.assertNotIn("SITE_DESCRIPTION, SITE_NAME", source)
        self.assertIn("GoreeCloud Projects | Project planning and delivery", source)


if __name__ == "__main__":
    unittest.main()
