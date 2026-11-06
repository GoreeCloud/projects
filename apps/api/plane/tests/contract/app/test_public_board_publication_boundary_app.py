# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Full Plane/Django contract checks for public-board publication boundaries.

These tests deliberately use the application's actual ORM, URL router, and
DRF middleware. They require the configured isolated PostgreSQL test database
and must never be pointed at production.
"""
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from plane.db.models import DeployBoard, Project, Workspace


@pytest.fixture
def published_project(db, workspace):
    return Project.objects.create(
        name="Published Board Project",
        identifier=f"P{uuid4().hex[:6].upper()}",
        workspace=workspace,
    )


@pytest.fixture
def published_board(db, workspace, published_project):
    return DeployBoard.objects.create(
        workspace=workspace,
        project=published_project,
        entity_name="project",
        entity_identifier=published_project.id,
    )


def public_url(board, suffix="meta/"):
    return f"/api/public/anchor/{board.anchor}/{suffix}"


@pytest.mark.contract
@pytest.mark.django_db
class TestPublicBoardPublicationBoundary:
    def test_disable_revokes_existing_anchor_on_next_request(self, session_client, published_board):
        url = public_url(published_board)
        assert session_client.get(url).status_code == status.HTTP_200_OK

        DeployBoard.objects.filter(pk=published_board.pk).update(is_disabled=True)

        assert session_client.get(url).status_code == status.HTTP_404_NOT_FOUND

    def test_deleted_board_is_not_visible(self, session_client, published_board):
        url = public_url(published_board)
        DeployBoard.objects.filter(pk=published_board.pk).update(deleted_at=timezone.now())

        assert session_client.get(url).status_code == status.HTTP_404_NOT_FOUND

    def test_deleted_project_revokes_board_on_next_request(
        self, session_client, published_project, published_board
    ):
        url = public_url(published_board)
        assert session_client.get(url).status_code == status.HTTP_200_OK

        Project.objects.filter(pk=published_project.pk).update(deleted_at=timezone.now())

        assert session_client.get(url).status_code == status.HTTP_404_NOT_FOUND

    def test_deleted_workspace_revokes_board_on_next_request(
        self, session_client, workspace, published_board
    ):
        url = public_url(published_board)
        assert session_client.get(url).status_code == status.HTTP_200_OK

        Workspace.objects.filter(pk=workspace.pk).update(deleted_at=timezone.now())

        assert session_client.get(url).status_code == status.HTTP_404_NOT_FOUND

    def test_board_moved_to_another_workspace_is_not_public(
        self, session_client, create_user, published_board
    ):
        other = Workspace.objects.create(
            name="Unrelated Workspace",
            slug=f"unrelated-{uuid4().hex[:8]}",
            owner=create_user,
        )
        DeployBoard.objects.filter(pk=published_board.pk).update(workspace=other)

        assert session_client.get(public_url(published_board)).status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize("suffix", ("meta/", "settings/", "members/"))
    def test_disabled_board_is_denied_across_public_handlers(self, session_client, published_board, suffix):
        DeployBoard.objects.filter(pk=published_board.pk).update(is_disabled=True)

        assert session_client.get(public_url(published_board, suffix)).status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_reader_cannot_access_disabled_anchor(self, published_board):
        DeployBoard.objects.filter(pk=published_board.pk).update(is_disabled=True)
        anonymous_client = APIClient()

        assert anonymous_client.get(public_url(published_board)).status_code == status.HTTP_404_NOT_FOUND
