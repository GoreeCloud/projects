# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""HTTP-dispatch smoke tests for the actual shared Plane public-board gate.

Uses DRF APIRequestFactory and a synthetic in-memory SQLite board model.
It does not import Plane's application services or contact user databases.
"""
import ast
import importlib.util
from pathlib import Path
import unittest
from uuid import uuid4

SOURCE = Path(__file__).resolve().parents[1] / "apps/api/plane/space/views/base.py"


@unittest.skipUnless(
    importlib.util.find_spec("django") is not None
    and importlib.util.find_spec("rest_framework") is not None,
    "Django and Django REST Framework required",
)
class PublicBoardDRFDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
                SECRET_KEY="synthetic-public-board-test-only",
                USE_TZ=True,
                REST_FRAMEWORK={"UNAUTHENTICATED_USER": None},
            )
        import django
        django.setup()
        from django.db import connection, models
        from rest_framework.exceptions import NotFound
        from rest_framework.permissions import AllowAny
        from rest_framework.response import Response
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView

        cls.connection = connection
        cls.Workspace = type("SyntheticDRFWorkspace", (models.Model,), {
            "__module__": __name__,
            "id": models.UUIDField(primary_key=True, default=uuid4),
            "deleted_at": models.DateTimeField(null=True),
            "Meta": type("Meta", (), {
                "app_label": "gc_public_board_drf_test",
                "db_table": "gc_drf_workspace_smoke_only",
            }),
        })
        cls.Project = type("SyntheticDRFProject", (models.Model,), {
            "__module__": __name__,
            "id": models.UUIDField(primary_key=True, default=uuid4),
            "workspace": models.ForeignKey(cls.Workspace, on_delete=models.CASCADE),
            "deleted_at": models.DateTimeField(null=True),
            "Meta": type("Meta", (), {
                "app_label": "gc_public_board_drf_test",
                "db_table": "gc_drf_project_smoke_only",
            }),
        })
        cls.Board = type(
            "SyntheticDRFPublicBoard",
            (models.Model,),
            {
                "__module__": __name__,
                "anchor": models.CharField(max_length=255, unique=True),
                "entity_name": models.CharField(max_length=30),
                "project": models.ForeignKey(cls.Project, on_delete=models.CASCADE),
                "workspace": models.ForeignKey(cls.Workspace, on_delete=models.CASCADE),
                "entity_identifier": models.UUIDField(),
                "deleted_at": models.DateTimeField(null=True),
                "is_disabled": models.BooleanField(default=False),
                "Meta": type("Meta", (), {
                    "app_label": "gc_public_board_drf_test",
                    "db_table": "gc_drf_public_board_smoke_only",
                }),
            },
        )
        with connection.schema_editor() as editor:
            for model in (cls.Workspace, cls.Project, cls.Board):
                editor.create_model(model)

        tree = ast.parse(SOURCE.read_text())
        original = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                        and node.name == "DeployBoardAnchorMixin")
        namespace = {
            "DeployBoard": cls.Board,
            "F": models.F,
            "NotFound": NotFound,
        }
        module = ast.fix_missing_locations(ast.Module(body=[original], type_ignores=[]))
        exec(compile(module, str(SOURCE), "exec"), namespace)
        guard_mixin = namespace["DeployBoardAnchorMixin"]

        def get(self, request, anchor):
            return Response({"published": True})

        def no_authentication(self, request):
            # No production login, sessions or user tables are loaded.
            return None

        cls.Probe = type(
            "SyntheticPublicBoardHTTPProbe",
            (guard_mixin, APIView),
            {
                "authentication_classes": [],
                "permission_classes": [AllowAny],
                "perform_authentication": no_authentication,
                "get": get,
            },
        )
        cls.request_factory = APIRequestFactory()

    @classmethod
    def tearDownClass(cls):
        with cls.connection.schema_editor() as editor:
            for model in (cls.Board, cls.Project, cls.Workspace):
                editor.delete_model(model)

    def tearDown(self):
        self.Board.objects.all().delete()
        self.Project.objects.all().delete()
        self.Workspace.objects.all().delete()

    def request_board(self, anchor):
        request = self.request_factory.get("/anchor/" + anchor + "/meta/")
        return self.Probe.as_view()(request, anchor=anchor)

    def test_enabled_project_board_returns_http_200(self):
        workspace = self.Workspace.objects.create()
        project = self.Project.objects.create(workspace=workspace)
        self.Board.objects.create(
            anchor="published", entity_name="project",
            project=project, workspace=workspace,
            entity_identifier=project.pk,
            is_disabled=False, deleted_at=None,
        )
        response = self.request_board("published")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"published": True})

    def test_unpublish_revokes_access_on_next_request(self):
        # Verify database state is consulted for each request rather than
        # caching a previously accepted publication anchor in the view.
        workspace = self.Workspace.objects.create()
        project = self.Project.objects.create(workspace=workspace)
        board = self.Board.objects.create(
            anchor="published", entity_name="project",
            project=project, workspace=workspace,
            entity_identifier=project.pk,
            is_disabled=False, deleted_at=None,
        )
        self.assertEqual(self.request_board("published").status_code, 200)
        self.Board.objects.filter(pk=board.pk).update(is_disabled=True)
        self.assertEqual(self.request_board("published").status_code, 404)

        self.Board.objects.filter(pk=board.pk).update(is_disabled=False)
        self.assertEqual(self.request_board("published").status_code, 200)
        from django.utils import timezone
        self.Project.objects.filter(pk=project.pk).update(deleted_at=timezone.now())
        self.assertEqual(self.request_board("published").status_code, 404)

    def test_revoked_and_invalid_boards_return_http_404(self):
        from django.utils import timezone
        cases = (
            "missing", "disabled", "deleted_board", "non_project",
            "identity_mismatch", "deleted_project", "deleted_workspace",
            "cross_workspace",
        )
        for case in cases:
            with self.subTest(case=case):
                self.tearDown()
                if case != "missing":
                    workspace = self.Workspace.objects.create()
                    project = self.Project.objects.create(workspace=workspace)
                    fields = {
                        "anchor": "published", "entity_name": "project",
                        "project": project, "workspace": workspace,
                        "entity_identifier": project.pk,
                        "is_disabled": False, "deleted_at": None,
                    }
                    if case == "disabled":
                        fields["is_disabled"] = True
                    elif case == "deleted_board":
                        fields["deleted_at"] = timezone.now()
                    elif case == "non_project":
                        fields["entity_name"] = "module"
                    elif case == "identity_mismatch":
                        fields["entity_identifier"] = uuid4()
                    elif case == "deleted_project":
                        project.deleted_at = timezone.now()
                        project.save(update_fields=["deleted_at"])
                    elif case == "deleted_workspace":
                        workspace.deleted_at = timezone.now()
                        workspace.save(update_fields=["deleted_at"])
                    elif case == "cross_workspace":
                        fields["workspace"] = self.Workspace.objects.create()
                    self.Board.objects.create(**fields)
                response = self.request_board("published")
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("published", response.data)


if __name__ == "__main__":
    unittest.main()
