# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Static inventory test for Plane Space routes guarded by the anchor mixin."""
import ast
from pathlib import Path
import unittest

SPACE = Path(__file__).resolve().parents[1] / "apps/api/plane/space"
GUARDED_BASES = {"BaseAPIView", "BaseViewSet"}


def public_anchor_routes():
    handlers = {}
    for path in (SPACE / "views").glob("*.py"):
        tree = ast.parse(path.read_text())
        for item in tree.body:
            if isinstance(item, ast.ClassDef):
                handlers[item.name] = {ast.unparse(base) for base in item.bases}

    routes = []
    for path in (SPACE / "urls").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id != "path" or len(node.args) < 2:
                continue
            route = node.args[0]
            if not isinstance(route, ast.Constant) or "<str:anchor>" not in str(route.value):
                continue
            handler_call = node.args[1]
            target = None
            if (isinstance(handler_call, ast.Call)
                    and isinstance(handler_call.func, ast.Attribute)
                    and handler_call.func.attr == "as_view"
                    and isinstance(handler_call.func.value, ast.Name)):
                target = handler_call.func.value.id
            routes.append((str(path.relative_to(SPACE)), route.value, target, handlers.get(target, set())))
    return routes


class PublicAnchorRouteCoverageTests(unittest.TestCase):
    def test_all_public_anchor_routes_use_the_guarded_view_bases(self):
        routes = public_anchor_routes()
        self.assertGreaterEqual(len(routes), 23, "Public Space route inventory unexpectedly shrank")
        for file_name, route, handler, bases in routes:
            with self.subTest(path=file_name, route=route, handler=handler):
                self.assertIsNotNone(handler, "Unresolved public anchor handler")
                self.assertTrue(
                    bases & GUARDED_BASES,
                    f"{handler} must inherit BaseAPIView or BaseViewSet and thus DeployBoardAnchorMixin",
                )

    def test_shared_base_classes_retain_the_mixin(self):
        tree = ast.parse((SPACE / "views/base.py").read_text())
        classes = {item.name: {ast.unparse(base) for base in item.bases}
                   for item in tree.body if isinstance(item, ast.ClassDef)}
        for name in GUARDED_BASES:
            with self.subTest(base=name):
                self.assertIn(name, classes)
                self.assertIn("DeployBoardAnchorMixin", classes[name])


if __name__ == "__main__":
    unittest.main()
