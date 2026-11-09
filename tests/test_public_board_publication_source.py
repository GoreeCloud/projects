# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Static source contracts for four scoped anonymous Space routes.

These checks do NOT replace Django/PostgreSQL HTTP, tenant, revocation, or
browser acceptance tests. The full security/release gate remains open.
"""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPACE = ROOT / "apps/api/plane/space"


def method(name):
    tree = ast.parse((SPACE / "views/project.py").read_text())
    klass = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)
    return next(node for node in klass.body if isinstance(node, ast.FunctionDef) and node.name == "get")


def route(handler, path):
    tree = ast.parse((SPACE / "urls" / path).read_text())
    matches = []
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != "path":
            continue
        if len(call.args) < 2 or not isinstance(call.args[0], ast.Constant):
            continue
        if ast.unparse(call.args[1]) == handler + ".as_view()":
            matches.append(call.args[0].value)
    if len(matches) != 1:
        raise AssertionError(f"Expected one {handler} route, found {len(matches)}")
    return matches[0]


def orm_call(node, manager, verb):
    return [
        call for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
        and call.func.attr == verb and ast.unparse(call.func.value) == manager
    ]


def keywords(call):
    return {kw.arg: ast.unparse(kw.value) for kw in call.keywords if kw.arg is not None}


PUBLICATION = {
    "workspace__slug": "slug",
    "entity_name": "'project'",
    "entity_identifier": "F('project_id')",
    "is_disabled": "False",
    "deleted_at__isnull": "True",
    "project__deleted_at__isnull": "True",
    "workspace__deleted_at__isnull": "True",
    "project__workspace_id": "F('workspace_id')",
}


class AnonymousBoardRoutingTests(unittest.TestCase):
    def test_workspace_listing_slug_matches_django_route(self):
        value = route("WorkspaceProjectDeployBoardEndpoint", "intake.py")
        self.assertEqual(value, "workspaces/<str:slug>/project-boards/")
        self.assertEqual([a.arg for a in method("WorkspaceProjectDeployBoardEndpoint").args.args],
                         ["self", "request", *re.findall(r"<[^:>]+:([^>]+)>", value)])

    def test_workspace_listing_only_returns_live_publications(self):
        view = method("WorkspaceProjectDeployBoardEndpoint")
        self.assertFalse(any(
            isinstance(item, (ast.Assign, ast.AnnAssign))
            and isinstance(item.value, ast.Attribute) and item.value.attr == "values_list"
            for item in ast.walk(view)
        ))
        projects = orm_call(view, "Project.objects", "filter")
        boards = orm_call(view, "DeployBoard.objects", "filter")
        self.assertEqual(len(projects), 1)
        self.assertEqual(len(boards), 1)
        self.assertTrue(any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "Exists" for node in ast.walk(view)
        ))
        self.assertEqual(keywords(projects[0]), {
            "workspace__slug": "slug",
            "workspace__deleted_at__isnull": "True",
            "deleted_at__isnull": "True",
        })
        self.assertEqual(keywords(boards[0]), {
            **PUBLICATION, "project_id": "OuterRef('pk')",
        })

    def test_anchor_lookup_signature_matches_django_route(self):
        value = route("WorkspaceProjectAnchorEndpoint", "project.py")
        self.assertEqual(value, "workspaces/<str:slug>/projects/<uuid:project_id>/anchor/")
        self.assertEqual([a.arg for a in method("WorkspaceProjectAnchorEndpoint").args.args],
                         ["self", "request", *re.findall(r"<[^:>]+:([^>]+)>", value)])

    def test_public_settings_and_member_routes_accept_only_anchor(self):
        for handler, expected in (
            ("ProjectDeployBoardPublicSettingsEndpoint", "anchor/<str:anchor>/settings/"),
            ("ProjectMembersEndpoint", "anchor/<str:anchor>/members/"),
        ):
            with self.subTest(handler=handler):
                value = route(handler, "project.py")
                self.assertEqual(value, expected)
                self.assertEqual([argument.arg for argument in method(handler).args.args],
                                 ["self", "request", "anchor"])

    def test_public_settings_and_member_routes_require_active_project_publication(self):
        required = {
            name: value for name, value in PUBLICATION.items()
            if name != "workspace__slug"
        }
        for handler, verb in (
            ("ProjectDeployBoardPublicSettingsEndpoint", "get"),
            ("ProjectMembersEndpoint", "filter"),
        ):
            with self.subTest(handler=handler):
                view = method(handler)
                predicates = orm_call(view, "DeployBoard.objects", verb)
                self.assertEqual(len(predicates), 1)
                self.assertEqual(keywords(predicates[0]), {"anchor": "anchor", **required})
        # The members endpoint must restrict its data source to active
        # records on the selected publication's project AND workspace.
        view = method("ProjectMembersEndpoint")
        members = orm_call(view, "ProjectMember.objects", "filter")
        self.assertEqual(len(members), 1)
        self.assertEqual(keywords(members[0]), {
            "project": "deploy_board.project",
            "workspace": "deploy_board.workspace",
            "is_active": "True",
        })

    def test_anonymous_anchor_lookup_enforces_current_publication(self):
        view = method("WorkspaceProjectAnchorEndpoint")
        matches = orm_call(view, "DeployBoard.objects", "get")
        self.assertEqual(len(matches), 1)
        self.assertEqual(keywords(matches[0]), {
            **PUBLICATION, "project_id": "project_id",
            "entity_identifier": "project_id",
        })


if __name__ == "__main__":
    unittest.main()
