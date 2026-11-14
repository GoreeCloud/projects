# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""AST contracts for anonymous issue and interaction board publication.

This tests actual view source structure, not full Plane/PostgreSQL acceptance.
"""
import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "apps/api/plane/space/views/issue.py"

def calls(node, path):
    return [n for n in ast.walk(node) if isinstance(n, ast.Call)
            and ast.unparse(n.func) == path]

class IssueAnchorSourceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(SOURCE.read_text())
        cls.helper = next(n for n in cls.tree.body
                          if isinstance(n, ast.FunctionDef)
                          and n.name == "_published_project_board_queryset")

    def test_shared_guard_requires_current_published_project(self):
        lookups = calls(self.helper, "DeployBoard.objects.filter")
        self.assertEqual(len(lookups), 1)
        fields = {kw.arg: ast.unparse(kw.value) for kw in lookups[0].keywords}
        self.assertEqual(fields, {
            "anchor": "anchor",
            "entity_name": "'project'",
            "entity_identifier": "F('project_id')",
            "is_disabled": "False",
            "deleted_at__isnull": "True",
            "project__deleted_at__isnull": "True",
            "workspace__deleted_at__isnull": "True",
            "project__workspace_id": "F('workspace_id')",
        })

    def test_every_public_issue_handler_uses_shared_guard_and_never_raw_board_manager(self):
        total = 0
        names = {
            "ProjectIssuesPublicEndpoint", "IssueRetrievePublicEndpoint",
            "IssueCommentPublicViewSet", "IssueReactionPublicViewSet",
            "CommentReactionPublicViewSet", "IssueVotePublicViewSet",
        }
        for klass in (n for n in self.tree.body if isinstance(n, ast.ClassDef)):
            if klass.name not in names:
                continue
            self.assertEqual(calls(klass, "DeployBoard.objects.get"), [], klass.name)
            self.assertEqual(calls(klass, "DeployBoard.objects.filter"), [], klass.name)
            count = len(calls(klass, "_published_project_board_queryset"))
            self.assertGreater(count, 0, klass.name)
            total += count
        self.assertEqual(total, 15)

    def test_public_issue_read_does_not_query_issue_before_publication_guard(self):
        for name in ("ProjectIssuesPublicEndpoint", "IssueRetrievePublicEndpoint"):
            klass = next(n for n in self.tree.body
                         if isinstance(n, ast.ClassDef) and n.name == name)
            method = next(n for n in klass.body
                          if isinstance(n, ast.FunctionDef) and n.name == "get")
            guard = calls(method, "_published_project_board_queryset")
            query = calls(method, "Issue.issue_objects.filter")
            self.assertEqual(len(guard), 1)
            self.assertGreaterEqual(len(query), 1)
            self.assertTrue(all(guard[0].lineno < call.lineno for call in query))

    def test_reaction_and_vote_lists_bind_real_anchor_and_board_workspace(self):
        for name in ("IssueReactionPublicViewSet", "IssueVotePublicViewSet"):
            klass = next(n for n in self.tree.body
                         if isinstance(n, ast.ClassDef) and n.name == name)
            method = next(n for n in klass.body
                          if isinstance(n, ast.FunctionDef) and n.name == "get_queryset")
            lookups = calls(method, "_published_project_board_queryset")
            self.assertEqual(len(lookups), 1)
            self.assertEqual(ast.unparse(lookups[0].args[0]),
                             "self.kwargs.get('anchor')")
            lookups = [(k.arg, ast.unparse(k.value))
                       for n in ast.walk(method) if isinstance(n, ast.Call)
                       for k in n.keywords]
            self.assertIn(("workspace_id", "project_deploy_board.workspace_id"), lookups)
            self.assertIn(("project_id", "project_deploy_board.project_id"), lookups)

if __name__ == "__main__":
    unittest.main()
