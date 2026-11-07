# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""PENDING (red) static release gates for unanchored public-board routes.

Run explicitly:
    python3 -m unittest discover -s acceptance -p 'pending_public_board_routes.py' -v

This file deliberately lives OUTSIDE tests/ because the Plane import still
violates these gates. Do not mark the application accepted while they fail.
This is source-contract review, not a Django/PostgreSQL HTTP penetration test.
"""
import ast
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPACE = ROOT / "apps/api/plane/space"
VIEWS = SPACE / "views/project.py"
INTAKE_ROUTES = SPACE / "urls/intake.py"
PROJECT_ROUTES = SPACE / "urls/project.py"


def load_methods():
    tree = ast.parse(VIEWS.read_text())
    return {
        node.name: next(
            (child for child in node.body if isinstance(child, ast.FunctionDef)
             and child.name == "get"), None
        )
        for node in tree.body if isinstance(node, ast.ClassDef)
    }


def route_path_for(handler, file_path):
    tree = ast.parse(file_path.read_text())
    matching = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "path" and len(node.args) >= 2
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            continue
        value = node.args[1]
        if (isinstance(value, ast.Call)
                and isinstance(value.func, ast.Attribute)
                and value.func.attr == "as_view"
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id == handler):
            matching.append(node.args[0].value)
    if len(matching) != 1:
        raise AssertionError(
            f"Expected one route for {handler}; got {len(matching)}"
        )
    return matching[0]


def keyword_names(method):
    return {
        kw.arg
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"get", "filter", "exclude"}
        for kw in node.keywords if kw.arg is not None
    }


def explicit_denial(method):
    # An endpoint which unconditionally raises NotFound is a permissible
    # temporary fail-closed alternative to exposing an unreviewed capability.
    return any(
        isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
        and node.exc.func.id in {"NotFound", "Http404"}
        for node in ast.walk(method)
    )


class PendingUnanchoredPublicBoardReleaseGates(unittest.TestCase):
    def test_workspace_board_list_route_kwargs_match_handler(self):
        route = route_path_for(
            "WorkspaceProjectDeployBoardEndpoint", INTAKE_ROUTES
        )
        self.assertEqual(route, "workspaces/<str:slug>/project-boards/")
        method = load_methods()["WorkspaceProjectDeployBoardEndpoint"]
        self.assertIsNotNone(method)
        bound_args = [arg.arg for arg in method.args.args][2:]
        url_kwargs = re.findall(r"<[^:>]+:([^>]+)>", route)
        self.assertEqual(
            bound_args, url_kwargs,
            "The public URL passes slug, but the handler signature differs.",
        )

    def test_workspace_board_list_never_uses_unbound_values_list_method(self):
        method = load_methods()["WorkspaceProjectDeployBoardEndpoint"]
        uncalled = [
            node for node in ast.walk(method)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "values_list"
        ]
        self.assertFalse(
            uncalled,
            "A bare .values_list method is not a DeployBoard instance or queryset.",
        )

    def test_workspace_board_list_is_publication_scoped_or_disabled(self):
        method = load_methods()["WorkspaceProjectDeployBoardEndpoint"]
        if explicit_denial(method):
            return
        fields = keyword_names(method)
        required = {
            "workspace__slug", "entity_name", "is_disabled",
            "deleted_at__isnull", "project__deleted_at__isnull",
            "workspace__deleted_at__isnull", "project__workspace_id",
            "entity_identifier",
        }
        self.assertFalse(
            required - fields,
            "Anonymous workspace board enumeration must fail closed or "
            f"establish all publication and tenant predicates: {sorted(required - fields)}",
        )

    def test_slug_project_anchor_lookup_is_publication_scoped_or_disabled(self):
        route = route_path_for("WorkspaceProjectAnchorEndpoint", PROJECT_ROUTES)
        self.assertEqual(
            route, "workspaces/<str:slug>/projects/<uuid:project_id>/anchor/"
        )
        method = load_methods()["WorkspaceProjectAnchorEndpoint"]
        self.assertEqual(
            [arg.arg for arg in method.args.args][2:], ["slug", "project_id"]
        )
        if explicit_denial(method):
            return
        fields = keyword_names(method)
        required = {
            "workspace__slug", "project_id", "entity_identifier",
            "entity_name", "is_disabled", "deleted_at__isnull",
            "project__deleted_at__isnull",
            "workspace__deleted_at__isnull", "project__workspace_id",
        }
        self.assertFalse(
            required - fields,
            "Anonymous anchor discovery must fail closed or check actual "
            f"publication and tenant state: {sorted(required - fields)}",
        )


if __name__ == "__main__":
    unittest.main()
