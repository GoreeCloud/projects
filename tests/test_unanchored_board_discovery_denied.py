# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Source-owned fail-closed gate for two unanchored anonymous Space routes.

No application, network, database, secrets or third-party imports are needed.
These tests do not establish full Plane/PostgreSQL or browser acceptance.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPACE = ROOT / "apps/api/plane/space"
SOURCE = SPACE / "views/project.py"
DENIED = {
    "WorkspaceProjectDeployBoardEndpoint": (
        "intake.py",
        "workspaces/<str:slug>/project-boards/",
        ("self", "request", "slug"),
    ),
    "WorkspaceProjectAnchorEndpoint": (
        "project.py",
        "workspaces/<str:slug>/projects/<uuid:project_id>/anchor/",
        ("self", "request", "slug", "project_id"),
    ),
}


def get_method(handler):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == handler)
    return next(node for node in cls.body
                if isinstance(node, ast.FunctionDef) and node.name == "get")


def route_for(handler, url_file):
    tree = ast.parse((SPACE / "urls" / url_file).read_text(encoding="utf-8"))
    result = []
    for call in ast.walk(tree):
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                and call.func.id == "path" and len(call.args) >= 2):
            continue
        view = call.args[1]
        if (isinstance(view, ast.Call) and isinstance(view.func, ast.Attribute)
                and view.func.attr == "as_view"
                and isinstance(view.func.value, ast.Name)
                and view.func.value.id == handler):
            result.append(ast.literal_eval(call.args[0]))
    return result


class UnanchoredDiscoveryFailClosedTests(unittest.TestCase):
    def test_both_live_url_routes_are_deny_only(self):
        for handler, (file_name, url, _args) in DENIED.items():
            with self.subTest(handler=handler):
                self.assertEqual(route_for(handler, file_name), [url])

    def test_signatures_match_django_kwargs_and_have_no_queries(self):
        for handler, (_file_name, _url, signature) in DENIED.items():
            with self.subTest(handler=handler):
                method = get_method(handler)
                self.assertEqual(tuple(arg.arg for arg in method.args.args), signature)
                self.assertEqual(len(method.body), 1, "No branches or DB calls may precede denial")
                self.assertIsInstance(method.body[0], ast.Return)
                self.assertEqual(
                    ast.unparse(method.body[0].value),
                    "Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)",
                )

    def test_actual_extracted_handlers_return_404_without_plane_or_database(self):
        for handler, (_file_name, _url, signature) in DENIED.items():
            with self.subTest(handler=handler):
                method = get_method(handler)
                method.decorator_list = []
                module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
                namespace = {
                    "Response": lambda payload, status: (payload, status),
                    "status": SimpleNamespace(HTTP_404_NOT_FOUND=404),
                }
                exec(compile(module, str(SOURCE), "exec"), namespace)
                args = tuple("synthetic-no-secret" for _ in signature)
                self.assertEqual(namespace["get"](*args), ({"error": "Not found"}, 404))

    def test_other_anchored_board_view_is_not_replaced_by_deny_handler(self):
        method = get_method("ProjectDeployBoardPublicSettingsEndpoint")
        self.assertNotEqual(
            ast.unparse(method.body[-1]),
            "return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)",
        )


if __name__ == "__main__":
    unittest.main()
