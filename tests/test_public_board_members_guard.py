# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Isolated execution tests of the imported public-board member view.

The actual method body is loaded by Python AST. Django and Plane services are
not imported; fake querysets exercise response decisions and filter contracts.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps/api/plane/space/views/project.py"
EXPECTED_FILTERS = {
    "anchor", "entity_name", "entity_identifier", "is_disabled",
    "deleted_at__isnull",
}
EXPECTED_FIELDS = ("id", "member", "member__display_name", "member__avatar")


class FieldReference:
    def __init__(self, name):
        self.name = name


class Boards:
    def __init__(self, board):
        self.board = board
        self.filters = []

    def filter(self, **kwargs):
        self.filters.append(kwargs)
        board = self.board
        valid = bool(board)
        if board:
            for key, value in kwargs.items():
                if key == "deleted_at__isnull":
                    valid &= (board.deleted_at is None) == value
                elif isinstance(value, FieldReference):
                    valid &= getattr(board, key) == getattr(board, value.name)
                else:
                    valid &= getattr(board, key) == value
        self.match = board if valid else None
        return self

    def first(self):
        return self.match


class Members:
    def __init__(self):
        self.filters = []
        self.selected_fields = None

    def filter(self, **kwargs):
        self.filters.append(kwargs)
        return self

    def values(self, *fields):
        self.selected_fields = fields
        return [{"id": 3, "member": 4, "member__display_name": "Visible",
                 "member__avatar": None}]


def load_original_method(boards, members):
    tree = ast.parse(SOURCE.read_text())
    view = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                and n.name == "ProjectMembersEndpoint")
    method = next(n for n in view.body if isinstance(n, ast.FunctionDef)
                  and n.name == "get")
    method.decorator_list = []
    wrapped = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    namespace = {
        "DeployBoard": SimpleNamespace(objects=boards),
        "ProjectMember": SimpleNamespace(objects=members),
        "F": FieldReference,
        "Response": lambda data, status: SimpleNamespace(data=data, status_code=status),
        "status": SimpleNamespace(HTTP_404_NOT_FOUND=404, HTTP_200_OK=200),
    }
    exec(compile(wrapped, str(SOURCE), "exec"), namespace)
    return namespace["get"]


def make_board(**overrides):
    fields = {
        "anchor": "safe-anchor", "entity_name": "project",
        "entity_identifier": "project-id", "project_id": "project-id",
        "project": "project-object", "workspace": "workspace-object",
        "is_disabled": False, "deleted_at": None,
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


class PublicMemberScopeTests(unittest.TestCase):
    def invoke(self, board, anchor="safe-anchor"):
        boards = Boards(board)
        members = Members()
        result = load_original_method(boards, members)(object(), object(), anchor)
        self.assertEqual(set(boards.filters[0]), EXPECTED_FILTERS)
        self.assertEqual(boards.filters[0]["entity_name"], "project")
        self.assertFalse(boards.filters[0]["is_disabled"])
        self.assertTrue(boards.filters[0]["deleted_at__isnull"])
        field_ref = boards.filters[0]["entity_identifier"]
        self.assertIsInstance(field_ref, FieldReference)
        self.assertEqual(field_ref.name, "project_id")
        return result, members

    def test_enabled_project_anchor_lists_public_profile_fields_only(self):
        response, members = self.invoke(make_board())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(members.selected_fields, EXPECTED_FIELDS)
        self.assertEqual(members.filters, [{
            "project": "project-object", "workspace": "workspace-object",
            "is_active": True,
        }])
        self.assertNotIn("member__email", members.selected_fields)

    def test_invalid_and_non_project_boards_return_not_found(self):
        cases = [
            None,
            make_board(anchor="different-anchor"),
            make_board(entity_name="module"),
            make_board(is_disabled=True),
            make_board(deleted_at="deleted"),
            make_board(entity_identifier="different-project"),
        ]
        for case in cases:
            with self.subTest(case=case):
                response, members = self.invoke(case)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(members.filters, [])


if __name__ == "__main__":
    unittest.main()
