# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Isolated Django ORM acceptance for the imported public-board anchor mixin.

Uses a synthetic, in-memory project-board schema, never the Plane app database.
"""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from uuid import uuid4

SOURCE = Path(__file__).resolve().parents[1] / "apps/api/plane/space/views/base.py"


class NotFound(Exception):
    pass


class Parent:
    def initial(self, request, *args, **kwargs):
        self.parent_called = True


def get_actual_guard(board_model, F):
    tree = ast.parse(SOURCE.read_text())
    cls = next(item for item in tree.body
               if isinstance(item, ast.ClassDef) and item.name == "DeployBoardAnchorMixin")
    cls.bases = [ast.Name(id="Parent", ctx=ast.Load())]
    cls.keywords = []
    cls.decorator_list = []
    namespace = {
        "Parent": Parent,
        "DeployBoard": board_model,
        "F": F,
        "NotFound": NotFound,
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 str(SOURCE), "exec"), namespace)
    return namespace["DeployBoardAnchorMixin"]


@unittest.skipUnless(importlib.util.find_spec("django") is not None, "Django unavailable")
class PublicBoardDjangoQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="isolated-board-test-only",
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
                USE_TZ=True,
            )
        import django
        django.setup()
        from django.db import connection, models
        cls.connection = connection
        cls.F = models.F
        cls.Workspace = type("SyntheticBoardWorkspace", (models.Model,), {
            "__module__": __name__,
            "id": models.UUIDField(primary_key=True, default=uuid4),
            "deleted_at": models.DateTimeField(null=True),
            "Meta": type("Meta", (), {
                "app_label": "gc_synthetic_board", "db_table": "gc_board_workspace_only",
            }),
        })
        cls.Project = type("SyntheticBoardProject", (models.Model,), {
            "__module__": __name__,
            "id": models.UUIDField(primary_key=True, default=uuid4),
            "deleted_at": models.DateTimeField(null=True),
            "workspace": models.ForeignKey(cls.Workspace, on_delete=models.CASCADE),
            "Meta": type("Meta", (), {
                "app_label": "gc_synthetic_board", "db_table": "gc_board_project_only",
            }),
        })
        cls.Board = type(
            "SyntheticPublicBoard",
            (models.Model,),
            {
                "__module__": __name__,
                "anchor": models.CharField(max_length=255),
                "entity_name": models.CharField(max_length=30),
                "is_disabled": models.BooleanField(default=False),
                "deleted_at": models.DateTimeField(null=True),
                "workspace": models.ForeignKey(cls.Workspace, on_delete=models.CASCADE),
                "project": models.ForeignKey(cls.Project, on_delete=models.CASCADE),
                "entity_identifier": models.UUIDField(),
                "Meta": type("Meta", (), {
                    "app_label": "gc_synthetic_board",
                    "db_table": "gc_public_board_guard_test_only",
                }),
            },
        )
        with connection.schema_editor() as editor:
            for model in (cls.Workspace, cls.Project, cls.Board):
                editor.create_model(model)
        cls.Guard = get_actual_guard(cls.Board, cls.F)

    @classmethod
    def tearDownClass(cls):
        with cls.connection.schema_editor() as editor:
            for model in (cls.Board, cls.Project, cls.Workspace):
                editor.delete_model(model)

    def tearDown(self):
        self.Board.objects.all().delete()
        self.Project.objects.all().delete()
        self.Workspace.objects.all().delete()

    def invoke(self, anchor):
        view = self.Guard()
        try:
            view.initial(object(), anchor=anchor)
            return False
        except NotFound:
            return True

    def test_valid_board_matches_real_sql_queryset(self):
        workspace = self.Workspace.objects.create()
        project = self.Project.objects.create(workspace=workspace)
        self.Board.objects.create(
            anchor="sample", entity_name="project", is_disabled=False,
            deleted_at=None, project=project, workspace=workspace,
            entity_identifier=project.pk,
        )
        self.assertFalse(self.invoke("sample"))
        self.assertTrue(self.invoke("unknown"))

    def test_disabled_and_mismatched_anchors_deny_in_real_orm(self):
        from django.utils import timezone
        cases = (
            "non_project", "disabled", "deleted_board", "wrong_identifier",
            "deleted_project", "deleted_workspace", "cross_workspace",
        )
        for case in cases:
            with self.subTest(case=case):
                self.tearDown()
                workspace = self.Workspace.objects.create()
                project = self.Project.objects.create(workspace=workspace)
                board = self.Board.objects.create(
                    anchor="sample", entity_name="project", is_disabled=False,
                    deleted_at=None, project=project, workspace=workspace,
                    entity_identifier=project.pk,
                )
                if case == "non_project":
                    board.entity_name = "module"
                    board.save(update_fields=["entity_name"])
                elif case == "disabled":
                    board.is_disabled = True
                    board.save(update_fields=["is_disabled"])
                elif case == "deleted_board":
                    board.deleted_at = timezone.now()
                    board.save(update_fields=["deleted_at"])
                elif case == "wrong_identifier":
                    board.entity_identifier = uuid4()
                    board.save(update_fields=["entity_identifier"])
                elif case == "deleted_project":
                    project.deleted_at = timezone.now()
                    project.save(update_fields=["deleted_at"])
                elif case == "deleted_workspace":
                    workspace.deleted_at = timezone.now()
                    workspace.save(update_fields=["deleted_at"])
                elif case == "cross_workspace":
                    other = self.Workspace.objects.create()
                    board.workspace = other
                    board.save(update_fields=["workspace"])
                self.assertTrue(self.invoke("sample"), case)


if __name__ == "__main__":
    unittest.main()
