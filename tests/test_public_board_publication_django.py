# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Synthetic Django/DRF exercise of four actual anonymous Space view methods.

The model classes and database are disposable SQLite stand-ins; this does not
import Plane's application or prove PostgreSQL/production tenant isolation.
"""
import ast
import importlib.util
from pathlib import Path
import unittest
from uuid import uuid4

SOURCE = Path(__file__).resolve().parents[1] / "apps/api/plane/space/views/project.py"


@unittest.skipUnless(
    importlib.util.find_spec("django") is not None
    and importlib.util.find_spec("rest_framework") is not None,
    "Pinned Django and DRF test dependencies not installed",
)
class AnonymousPublicationQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
                SECRET_KEY="synthetic-public-board-only",
                USE_TZ=True,
                REST_FRAMEWORK={"UNAUTHENTICATED_USER": None},
            )
        import django
        django.setup()
        from django.db import connection, models
        from django.db.models import Exists, F, OuterRef
        from django.core.exceptions import ObjectDoesNotExist
        from rest_framework import status
        from rest_framework.permissions import AllowAny
        from rest_framework.response import Response
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView

        cls.connection = connection
        cls.Workspace = type("SyntheticSpaceWorkspace", (models.Model,), {
            "__module__": __name__,
            "id": models.UUIDField(primary_key=True, default=uuid4),
            "slug": models.CharField(max_length=80, unique=True),
            "deleted_at": models.DateTimeField(null=True),
            "Meta": type("Meta", (), {"app_label": "gc_public_space_only",
                                      "db_table": "gc_synthetic_space_ws"}),
        })
        cls.Project = type("SyntheticSpaceProject", (models.Model,), {
            "__module__": __name__,
            "id": models.UUIDField(primary_key=True, default=uuid4),
            "workspace": models.ForeignKey(cls.Workspace, on_delete=models.CASCADE),
            "deleted_at": models.DateTimeField(null=True),
            "identifier": models.CharField(max_length=12),
            "name": models.CharField(max_length=255),
            "description": models.TextField(default=""),
            "emoji": models.CharField(max_length=255, null=True),
            "icon_prop": models.JSONField(null=True),
            "cover_image": models.TextField(null=True),
            "Meta": type("Meta", (), {"app_label": "gc_public_space_only",
                                      "db_table": "gc_synthetic_space_project"}),
        })
        cls.Board = type("SyntheticSpaceBoard", (models.Model,), {
            "__module__": __name__,
            "id": models.UUIDField(primary_key=True, default=uuid4),
            "workspace": models.ForeignKey(cls.Workspace, on_delete=models.CASCADE),
            "project": models.ForeignKey(cls.Project, on_delete=models.CASCADE),
            "entity_identifier": models.UUIDField(null=True),
            "entity_name": models.CharField(max_length=30),
            "anchor": models.CharField(max_length=255, unique=True),
            "deleted_at": models.DateTimeField(null=True),
            "is_disabled": models.BooleanField(default=False),
            "Meta": type("Meta", (), {"app_label": "gc_public_space_only",
                                      "db_table": "gc_synthetic_space_board"}),
        })
        cls.Member = type("SyntheticSpaceMember", (models.Model,), {
            "__module__": __name__,
            "id": models.UUIDField(primary_key=True, default=uuid4),
            "display_name": models.CharField(max_length=80),
            "avatar": models.TextField(null=True),
            "Meta": type("Meta", (), {"app_label": "gc_public_space_only",
                                      "db_table": "gc_synthetic_space_member"}),
        })
        cls.ProjectMember = type("SyntheticSpaceProjectMember", (models.Model,), {
            "__module__": __name__,
            "id": models.UUIDField(primary_key=True, default=uuid4),
            "workspace": models.ForeignKey(cls.Workspace, on_delete=models.CASCADE),
            "project": models.ForeignKey(cls.Project, on_delete=models.CASCADE),
            "member": models.ForeignKey(cls.Member, on_delete=models.CASCADE),
            "is_active": models.BooleanField(default=True),
            "Meta": type("Meta", (), {"app_label": "gc_public_space_only",
                                      "db_table": "gc_synthetic_space_project_member"}),
        })
        with connection.schema_editor() as editor:
            for model in (cls.Workspace, cls.Project, cls.Board, cls.Member, cls.ProjectMember):
                editor.create_model(model)

        class SyntheticBaseAPIView(APIView):
            authentication_classes = []
            permission_classes = [AllowAny]

            def handle_exception(self, exc):
                # Mirror the observed Plane BaseAPIView ObjectDoesNotExist -> 404.
                # This synthetic test does NOT execute that full inherited base.
                if isinstance(exc, ObjectDoesNotExist):
                    return Response({"error": "Not found"}, status=404)
                return super().handle_exception(exc)

        class SyntheticSerializer:
            def __init__(self, board):
                self.data = {"anchor": board.anchor, "projectId": str(board.project_id)}

        tree = ast.parse(SOURCE.read_text())
        scope = {
            "SyntheticBaseAPIView": SyntheticBaseAPIView,
            "Project": cls.Project,
            "DeployBoard": cls.Board,
            "ProjectMember": cls.ProjectMember,
            "DeployBoardSerializer": SyntheticSerializer,
            "Exists": Exists, "F": F, "OuterRef": OuterRef,
            "Response": Response, "status": status, "AllowAny": AllowAny,
        }
        cls.views = {}
        for name in ("WorkspaceProjectDeployBoardEndpoint", "WorkspaceProjectAnchorEndpoint",
                     "ProjectDeployBoardPublicSettingsEndpoint", "ProjectMembersEndpoint"):
            original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
            original.bases = [ast.Name(id="SyntheticBaseAPIView", ctx=ast.Load())]
            original.keywords = []
            original.decorator_list = []
            isolated = ast.fix_missing_locations(ast.Module(body=[original], type_ignores=[]))
            exec(compile(isolated, str(SOURCE), "exec"), scope)
            cls.views[name] = scope[name].as_view()
        cls.factory = APIRequestFactory()

    @classmethod
    def tearDownClass(cls):
        with cls.connection.schema_editor() as editor:
            for model in (cls.ProjectMember, cls.Member, cls.Board, cls.Project, cls.Workspace):
                editor.delete_model(model)

    def tearDown(self):
        self.ProjectMember.objects.all().delete()
        self.Member.objects.all().delete()
        self.Board.objects.all().delete()
        self.Project.objects.all().delete()
        self.Workspace.objects.all().delete()

    def create_pair(self, slug="alpha", *, published=True):
        ws = self.Workspace.objects.create(slug=slug)
        project = self.Project.objects.create(workspace=ws, identifier="ALPHA", name="Private title")
        board = None
        if published:
            board = self.Board.objects.create(
                workspace=ws, project=project, entity_name="project",
                entity_identifier=project.id, anchor=uuid4().hex,
            )
        return ws, project, board

    def listed(self, slug):
        result = self.views["WorkspaceProjectDeployBoardEndpoint"](
            self.factory.get("/workspaces/" + slug + "/project-boards/"), slug=slug)
        self.assertEqual(result.status_code, 200)
        return list(result.data)

    def anchor(self, slug, project_id):
        return self.views["WorkspaceProjectAnchorEndpoint"](
            self.factory.get("/workspaces/" + slug + "/projects/" + str(project_id) + "/anchor/"),
            slug=slug, project_id=project_id)

    def settings(self, anchor):
        return self.views["ProjectDeployBoardPublicSettingsEndpoint"](
            self.factory.get("/anchor/" + anchor + "/settings/"), anchor=anchor)

    def members(self, anchor):
        return self.views["ProjectMembersEndpoint"](
            self.factory.get("/anchor/" + anchor + "/members/"), anchor=anchor)

    def test_public_settings_and_limited_members_are_accessible_only_while_published(self):
        ws, project, board = self.create_pair()
        profile = self.Member.objects.create(display_name="Fictional Person", avatar="avatar.svg")
        self.ProjectMember.objects.create(workspace=ws, project=project, member=profile, is_active=True)
        settings = self.settings(board.anchor)
        self.assertEqual(settings.status_code, 200)
        self.assertEqual(settings.data["anchor"], board.anchor)
        members = self.members(board.anchor)
        self.assertEqual(members.status_code, 200)
        entries = list(members.data)
        self.assertEqual(len(entries), 1)
        self.assertEqual(set(entries[0]), {
            "id", "member", "member__display_name", "member__avatar"})
        self.assertEqual(entries[0]["member__display_name"], "Fictional Person")
        self.assertEqual(entries[0]["member"], profile.id)
        self.assertEqual(self.settings("missing-anchor").status_code, 404)
        self.assertEqual(self.members("missing-anchor").status_code, 404)

    def test_settings_and_member_directory_revoke_when_publication_changes(self):
        from django.utils import timezone
        ws, project, board = self.create_pair()
        profile = self.Member.objects.create(display_name="Synthetic Private", avatar=None)
        self.ProjectMember.objects.create(workspace=ws, project=project, member=profile, is_active=True)
        for field, value in (
            ("is_disabled", True), ("deleted_at", timezone.now()),
            ("entity_identifier", uuid4()), ("entity_name", "issue")
        ):
            old = getattr(board, field)
            setattr(board, field, value)
            board.save(update_fields=[field])
            with self.subTest(field=field):
                self.assertEqual(self.settings(board.anchor).status_code, 404)
                self.assertEqual(self.members(board.anchor).status_code, 404)
            setattr(board, field, old)
            board.save(update_fields=[field])
            self.assertEqual(self.settings(board.anchor).status_code, 200)
            self.assertEqual(self.members(board.anchor).status_code, 200)
        project.deleted_at = timezone.now()
        project.save(update_fields=["deleted_at"])
        self.assertEqual(self.settings(board.anchor).status_code, 404)
        self.assertEqual(self.members(board.anchor).status_code, 404)
        project.deleted_at = None
        project.save(update_fields=["deleted_at"])
        ws.deleted_at = timezone.now()
        ws.save(update_fields=["deleted_at"])
        self.assertEqual(self.settings(board.anchor).status_code, 404)
        self.assertEqual(self.members(board.anchor).status_code, 404)

    def test_inconsistent_workspace_id_cannot_expose_member_directory_or_settings(self):
        ws, project, board = self.create_pair()
        other = self.Workspace.objects.create(slug="other")
        profile = self.Member.objects.create(display_name="Private Profile", avatar=None)
        self.ProjectMember.objects.create(workspace=ws, project=project, member=profile, is_active=True)
        board.workspace = other
        board.save(update_fields=["workspace"])
        self.assertEqual(self.settings(board.anchor).status_code, 404)
        self.assertEqual(self.members(board.anchor).status_code, 404)

    def test_published_only_and_projection_does_not_expose_other_project_fields(self):
        ws, project, board = self.create_pair()
        self.Project.objects.create(workspace=ws, identifier="HIDDEN", name="Hidden unpublished")
        other_ws, other_project, other_board = self.create_pair("other")
        listed = self.listed("alpha")
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["id"], project.id)
        self.assertEqual(set(listed[0]), {"id", "identifier", "name", "description",
                                          "emoji", "icon_prop", "cover_image"})
        self.assertEqual(self.anchor("alpha", project.id).status_code, 200)
        self.assertEqual(self.anchor("alpha", project.id).data["anchor"], board.anchor)
        self.assertEqual(self.anchor("alpha", other_project.id).status_code, 404)
        self.assertEqual(self.listed("other")[0]["id"], other_project.id)

    def test_anonymous_access_revokes_immediately_on_disabled_deletion_or_wrong_identity(self):
        from django.utils import timezone
        workspace, project, board = self.create_pair()
        for field, value in (
            ("is_disabled", True),
            ("deleted_at", timezone.now()),
            ("entity_identifier", uuid4()),
            ("entity_name", "issue"),
        ):
            original = getattr(board, field)
            setattr(board, field, value)
            board.save(update_fields=[field])
            with self.subTest(field=field):
                self.assertEqual(self.listed("alpha"), [])
                self.assertEqual(self.anchor("alpha", project.id).status_code, 404)
            setattr(board, field, original)
            board.save(update_fields=[field])
            self.assertEqual(len(self.listed("alpha")), 1)
        project.deleted_at = timezone.now()
        project.save(update_fields=["deleted_at"])
        self.assertEqual(self.listed("alpha"), [])
        self.assertEqual(self.anchor("alpha", project.id).status_code, 404)
        project.deleted_at = None
        project.save(update_fields=["deleted_at"])
        workspace.deleted_at = timezone.now()
        workspace.save(update_fields=["deleted_at"])
        self.assertEqual(self.listed("alpha"), [])
        self.assertEqual(self.anchor("alpha", project.id).status_code, 404)

    def test_mismatched_owner_workspace_never_publishes_foreign_project(self):
        foreign, project, board = self.create_pair("foreign")
        other = self.Workspace.objects.create(slug="other")
        board.workspace = other
        board.save(update_fields=["workspace"])
        self.assertEqual(self.listed("foreign"), [])
        self.assertEqual(self.listed("other"), [])
        self.assertEqual(self.anchor("foreign", project.id).status_code, 404)
        self.assertEqual(self.anchor("other", project.id).status_code, 404)


if __name__ == "__main__":
    unittest.main()
