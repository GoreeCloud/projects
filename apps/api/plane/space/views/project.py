# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Django imports
# Third Party imports
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

# Module imports
from .base import BaseAPIView
from plane.app.serializers import DeployBoardSerializer
from plane.db.models import DeployBoard, ProjectMember


class ProjectDeployBoardPublicSettingsEndpoint(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, anchor):
        project_deploy_board = DeployBoard.objects.get(anchor=anchor, entity_name="project")
        serializer = DeployBoardSerializer(project_deploy_board)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkspaceProjectDeployBoardEndpoint(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        # Fail closed: this slug-only anonymous route cannot prove a deliberate
        # publication capability or user authorization. Do not enumerate any
        # workspace/project metadata until the complete Plane authorization and
        # revocation contract is reviewed and accepted.
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)


class WorkspaceProjectAnchorEndpoint(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, slug, project_id):
        # A guessed workspace slug/project UUID must not reveal a publication
        # anchor. This unauthenticated discovery route remains disabled while
        # tenant-scoped sharing and explicit GoreeShield consent are unresolved.
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)


class ProjectMembersEndpoint(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, anchor):
        deploy_board = DeployBoard.objects.filter(anchor=anchor).first()
        if not deploy_board:
            return Response(
                {"error": "Invalid anchor"},
                status=status.HTTP_404_NOT_FOUND,
            )

        members = ProjectMember.objects.filter(
            project=deploy_board.project,
            workspace=deploy_board.workspace,
            is_active=True,
        ).values(
            "id",
            "member",
            "member__display_name",
            "member__avatar",
        )
        return Response(members, status=status.HTTP_200_OK)
