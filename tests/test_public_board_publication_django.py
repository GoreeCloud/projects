# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Synthetic Django/DRF exercise of anonymous Space view methods.

The model classes are disposable stand-ins on SQLite by default or a separate,
explicitly selected CI-only PostgreSQL fixture. This does not import Plane's
application or prove full production tenant isolation.
"""
import ast
import importlib.util
import os
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
        # Never accept a caller-supplied DATABASE_URL or production DB target.
        # CI uses disposable fixed credentials against an ephemeral local-only
        # PostgreSQL service; outside that explicit mode use in-memory SQLite.
        backend = os.environ.get("GC_PUBLIC_BOARD_BACKEND", "sqlite")
        if backend not in ("sqlite", "postgres"):
            raise AssertionError("Unsupported synthetic public-board test backend")
        database = (
            {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "gc_public_board_test",
                "USER": "gc_public_board_test",
                "PASSWORD": "synthetic-public-board-test-only",
                "HOST": "127.0.0.1",
                "PORT": "5432",
                "CONN_MAX_AGE": 0,
            } if backend == "postgres" else
            {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        )
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[],
                DATABASES={"default": database},
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
        # Five additional anchor routes query project-scoped cycles, modules,
        # states and labels; only synthetic data, no Plane app models or DB.
        def ancillary(name, table, attrs):
            return type("SyntheticSpace" + name, (models.Model,), {
                "__module__": __name__,
                "id": models.UUIDField(primary_key=True, default=uuid4),
                "workspace": models.ForeignKey(cls.Workspace, on_delete=models.CASCADE),
                "project": models.ForeignKey(cls.Project, on_delete=models.CASCADE),
                **attrs,
                "Meta": type("Meta", (), {"app_label": "gc_public_space_only",
                                          "db_table": table}),
            })
        cls.Cycle = ancillary("Cycle", "gc_synthetic_space_cycle", {
            "name": models.CharField(max_length=80),
        })
        cls.Module = ancillary("Module", "gc_synthetic_space_module", {
            "name": models.CharField(max_length=80),
        })
        cls.State = ancillary("State", "gc_synthetic_space_state", {
            "name": models.CharField(max_length=80),
            "group": models.CharField(max_length=25),
            "color": models.CharField(max_length=10),
            "sequence": models.IntegerField(default=1),
        })
        cls.Label = ancillary("Label", "gc_synthetic_space_label", {
            "name": models.CharField(max_length=80),
            "color": models.CharField(max_length=10),
            "parent": models.UUIDField(null=True),
        })
        with connection.schema_editor() as editor:
            for model in (cls.Workspace, cls.Project, cls.Board, cls.Member,
                          cls.ProjectMember, cls.Cycle, cls.Module, cls.State, cls.Label):
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

        class SyntheticProjectSerializer:
            def __init__(self, project):
                self.data = {"id": str(project.id), "name": project.name}

        from django.db.models import Q
        tree = ast.parse(SOURCE.read_text())
        scope = {
            "Cycle": cls.Cycle, "Module": cls.Module,
            "State": cls.State, "Label": cls.Label, "Q": Q,
            "ProjectLiteSerializer": SyntheticProjectSerializer,
            "SyntheticBaseAPIView": SyntheticBaseAPIView,
            "Project": cls.Project,
            "DeployBoard": cls.Board,
            "ProjectMember": cls.ProjectMember,
            "DeployBoardSerializer": SyntheticSerializer,
            "Exists": Exists, "F": F, "OuterRef": OuterRef,
            "Response": Response, "status": status, "AllowAny": AllowAny,
        }
        # Execute only the extracted issue lookup helper against disposable
        # synthetic models. This does not import Plane or migrate its database.
        issue_source = SOURCE.parent / "issue.py"
        issue_tree = ast.parse(issue_source.read_text())
        helper = next(n for n in issue_tree.body if isinstance(n, ast.FunctionDef)
                      and n.name == "_published_project_board_queryset")
        isolated = ast.fix_missing_locations(ast.Module(body=[helper], type_ignores=[]))
        exec(compile(isolated, str(issue_source), "exec"), scope)
        cls.issue_board_lookup = staticmethod(scope["_published_project_board_queryset"])
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
        more_routes = {
            "ProjectCyclesEndpoint": "cycle.py",
            "ProjectModulesEndpoint": "module.py",
            "ProjectStatesEndpoint": "state.py",
            "ProjectLabelsEndpoint": "label.py",
            "ProjectMetaDataEndpoint": "meta.py",
        }
        for name, filename in more_routes.items():
            tree = ast.parse((SOURCE.parent / filename).read_text())
            original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
            original.bases = [ast.Name(id="SyntheticBaseAPIView", ctx=ast.Load())]
            original.keywords = []
            original.decorator_list = []
            isolated = ast.fix_missing_locations(ast.Module(body=[original], type_ignores=[]))
            exec(compile(isolated, str(SOURCE.parent / filename), "exec"), scope)
            cls.views[name] = scope[name].as_view()
        cls.factory = APIRequestFactory()

    @classmethod
    def tearDownClass(cls):
        with cls.connection.schema_editor() as editor:
            for model in (cls.Label, cls.State, cls.Module, cls.Cycle, cls.ProjectMember,
                          cls.Member, cls.Board, cls.Project, cls.Workspace):
                editor.delete_model(model)

    def test_runner_backend_cannot_silently_fall_back_to_sqlite(self):
        expected = os.environ.get("GC_PUBLIC_BOARD_BACKEND", "sqlite")
        self.assertEqual(self.connection.vendor, "postgresql" if expected == "postgres" else "sqlite")

    def tearDown(self):
        for model in (self.Label, self.State, self.Module, self.Cycle):
            model.objects.all().delete()
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

    def auxiliary(self, handler, anchor):
        return self.views[handler](
            self.factory.get("/anchor/" + anchor + "/scope/"), anchor=anchor)

    def test_cycles_modules_states_labels_and_metadata_are_only_published(self):
        ws, project, board = self.create_pair()
        other_ws, other_project, other_board = self.create_pair("unrelated")
        self.Cycle.objects.create(workspace=ws, project=project, name="Current cycle")
        self.Module.objects.create(workspace=ws, project=project, name="Current module")
        self.State.objects.create(workspace=ws, project=project, name="Started", group="started",
                                  color="#000000", sequence=2)
        self.State.objects.create(workspace=ws, project=project, name="Triage", group="backlog",
                                  color="#222222", sequence=1)
        self.Label.objects.create(workspace=ws, project=project, name="Work", color="#ffffff")
        # Similar named records from a different tenant must not leak.
        self.Cycle.objects.create(workspace=other_ws, project=other_project, name="Private cycle")
        for handler, expected_field in (
            ("ProjectCyclesEndpoint", "Current cycle"),
            ("ProjectModulesEndpoint", "Current module"),
            ("ProjectStatesEndpoint", "Started"),
            ("ProjectLabelsEndpoint", "Work"),
        ):
            with self.subTest(handler=handler):
                response = self.auxiliary(handler, board.anchor)
                self.assertEqual(response.status_code, 200)
                rows = list(response.data)
                self.assertEqual([row["name"] for row in rows], [expected_field])
                self.assertNotIn("Private cycle", str(rows))
                self.assertEqual(self.auxiliary(handler, "missing").status_code, 404)
        meta = self.auxiliary("ProjectMetaDataEndpoint", board.anchor)
        self.assertEqual(meta.status_code, 200)
        self.assertEqual(meta.data["id"], str(project.id))
        self.assertEqual(self.auxiliary("ProjectMetaDataEndpoint", "missing").status_code, 404)

    def test_five_auxiliary_public_routes_revoke_on_disabled_or_wrong_board(self):
        from django.utils import timezone
        ws, project, board = self.create_pair()
        handlers = (
            "ProjectCyclesEndpoint", "ProjectModulesEndpoint", "ProjectStatesEndpoint",
            "ProjectLabelsEndpoint", "ProjectMetaDataEndpoint",
        )
        for field, value in (
            ("is_disabled", True), ("deleted_at", timezone.now()),
            ("entity_name", "issue"), ("entity_identifier", uuid4())
        ):
            old = getattr(board, field)
            setattr(board, field, value)
            board.save(update_fields=[field])
            for handler in handlers:
                with self.subTest(handler=handler, field=field):
                    self.assertEqual(self.auxiliary(handler, board.anchor).status_code, 404)
            setattr(board, field, old)
            board.save(update_fields=[field])
        other_ws = self.Workspace.objects.create(slug="other")
        board.workspace = other_ws
        board.save(update_fields=["workspace"])
        for handler in handlers:
            self.assertEqual(self.auxiliary(handler, board.anchor).status_code, 404)
        board.workspace = ws
        board.save(update_fields=["workspace"])
        project.deleted_at = timezone.now()
        project.save(update_fields=["deleted_at"])
        for handler in handlers:
            self.assertEqual(self.auxiliary(handler, board.anchor).status_code, 404)
        project.deleted_at = None
        project.save(update_fields=["deleted_at"])
        ws.deleted_at = timezone.now()
        ws.save(update_fields=["deleted_at"])
        for handler in handlers:
            self.assertEqual(self.auxiliary(handler, board.anchor).status_code, 404)

    def test_issue_publication_guard_rejects_revoked_and_foreign_board(self):
        from django.utils import timezone
        workspace, project, board = self.create_pair()
        query = self.issue_board_lookup
        self.assertEqual(query(board.anchor).get().id, board.id)
        self.assertIsNone(query("unknown-anchor").first())
        for field, value in (
            ("is_disabled", True), ("deleted_at", timezone.now()),
            ("entity_identifier", uuid4()), ("entity_name", "issue"),
        ):
            saved = getattr(board, field)
            setattr(board, field, value)
            board.save(update_fields=[field])
            with self.subTest(field=field):
                self.assertIsNone(query(board.anchor).first())
                with self.assertRaises(self.Board.DoesNotExist):
                    query(board.anchor).get()
            setattr(board, field, saved)
            board.save(update_fields=[field])
            self.assertEqual(query(board.anchor).get().id, board.id)
        project.deleted_at = timezone.now()
        project.save(update_fields=["deleted_at"])
        self.assertIsNone(query(board.anchor).first())
        project.deleted_at = None
        project.save(update_fields=["deleted_at"])
        other = self.Workspace.objects.create(slug="foreign")
        board.workspace = other
        board.save(update_fields=["workspace"])
        self.assertIsNone(query(board.anchor).first())
        board.workspace = workspace
        board.save(update_fields=["workspace"])
        workspace.deleted_at = timezone.now()
        workspace.save(update_fields=["deleted_at"])
        self.assertIsNone(query(board.anchor).first())

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
