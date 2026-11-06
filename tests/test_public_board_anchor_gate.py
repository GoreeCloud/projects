# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Isolated tests for the actual shared Plane public-board anchor mixin.

Load and run the original mixin body with a fake ORM, not production Django.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "apps/api/plane/space/views/base.py"
REQUIRED = {
    "anchor", "entity_name", "is_disabled",
    "deleted_at__isnull", "entity_identifier",
}


class FieldReference:
    def __init__(self, name):
        self.name = name


class NotFound(Exception):
    pass


class Parent:
    def initial(self, request, *args, **kwargs):
        self.parent_calls = getattr(self, "parent_calls", 0) + 1


class FakeBoardManager:
    def __init__(self, board):
        self.board = board
        self.filters = []

    def filter(self, **kwargs):
        self.filters.append(kwargs)
        self.latest = kwargs
        return self

    def exists(self):
        board = self.board
        if board is None:
            return False
        for key, expected in self.latest.items():
            if key == "deleted_at__isnull":
                if (board.deleted_at is None) != expected:
                    return False
            elif isinstance(expected, FieldReference):
                if getattr(board, key) != getattr(board, expected.name):
                    return False
            elif getattr(board, key) != expected:
                return False
        return True


def load_original_mixin(manager):
    tree = ast.parse(SOURCE.read_text())
    cls = next(x for x in tree.body
               if isinstance(x, ast.ClassDef) and x.name == "DeployBoardAnchorMixin")
    cls.bases = [ast.Name(id="Parent", ctx=ast.Load())]
    cls.keywords = []
    cls.decorator_list = []
    source_ast = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    scope = {
        "Parent": Parent,
        "F": FieldReference,
        "DeployBoard": SimpleNamespace(objects=manager),
        "NotFound": NotFound,
    }
    exec(compile(source_ast, str(SOURCE), "exec"), scope)
    return scope["DeployBoardAnchorMixin"]


def board(**overrides):
    attributes = {
        "anchor": "valid-public-anchor",
        "entity_name": "project",
        "is_disabled": False,
        "deleted_at": None,
        "entity_identifier": "project-id",
        "project_id": "project-id",
    }
    attributes.update(overrides)
    return SimpleNamespace(**attributes)


class SharedBoardGateTests(unittest.TestCase):
    def invoke(self, record, *, anchor="valid-public-anchor"):
        manager = FakeBoardManager(record)
        view = load_original_mixin(manager)()
        try:
            view.initial(object(), anchor=anchor)
            rejected = False
        except NotFound:
            rejected = True
        self.assertEqual(view.parent_calls, 1)
        return rejected, manager

    def test_valid_public_project_board_is_accepted(self):
        rejected, manager = self.invoke(board())
        self.assertFalse(rejected)
        self.assertEqual(len(manager.filters), 1)
        filters = manager.filters[0]
        self.assertEqual(set(filters), REQUIRED)
        self.assertEqual(filters["entity_name"], "project")
        self.assertFalse(filters["is_disabled"])
        self.assertTrue(filters["deleted_at__isnull"])
        self.assertIsInstance(filters["entity_identifier"], FieldReference)
        self.assertEqual(filters["entity_identifier"].name, "project_id")

    def test_invalid_or_revoked_public_board_is_denied(self):
        examples = [
            None,
            board(anchor="other-anchor"),
            board(entity_name="module"),
            board(is_disabled=True),
            board(deleted_at="soft-deleted"),
            board(entity_identifier="wrong-id"),
        ]
        for record in examples:
            with self.subTest(record=record):
                rejected, manager = self.invoke(record)
                self.assertTrue(rejected)
                self.assertEqual(len(manager.filters), 1)

    def test_without_anchor_maintains_existing_private_route_behavior(self):
        rejected, manager = self.invoke(None, anchor=None)
        self.assertFalse(rejected)
        self.assertEqual(manager.filters, [])


if __name__ == "__main__":
    unittest.main()
