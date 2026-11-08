# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Green self-tests of the deliberately RED public-route acceptance analyzer.

Do not confuse passing analyzer tests with the four unresolved security gates.
"""
import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "goreecloud_pending_public_routes",
    ROOT / "acceptance/pending_public_board_routes.py",
)
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)


def method_from(source):
    tree = ast.parse(source)
    method = tree.body[0]
    if not isinstance(method, ast.FunctionDef):
        raise ValueError("Expected a single function")
    return method


class PublicBoardGateAnalyzerTests(unittest.TestCase):
    def test_accepts_strict_board_lookup_values(self):
        method = method_from('''
def get(self, request, slug, project_id):
    return DeployBoard.objects.filter(
        workspace__slug=slug,
        project_id=project_id,
        entity_identifier=F("project_id"),
        entity_name="project",
        is_disabled=False,
        deleted_at__isnull=True,
        project__deleted_at__isnull=True,
        workspace__deleted_at__isnull=True,
        project__workspace_id=F("workspace_id"),
    )
''')
        self.assertEqual(CHECKS.keyword_names(method), {
            "workspace__slug", "project_id", "entity_identifier", "entity_name",
            "is_disabled", "deleted_at__isnull", "project__deleted_at__isnull",
            "workspace__deleted_at__isnull", "project__workspace_id",
        })

    def test_exclude_does_not_supply_authorization_predicates(self):
        method = method_from('''
def get(self, request, slug):
    return DeployBoard.objects.exclude(
        is_disabled=False, deleted_at__isnull=True,
        entity_name="project",
    )
''')
        self.assertEqual(CHECKS.keyword_names(method), set())

    def test_reversed_boolean_and_wrong_entity_values_fail_closed(self):
        method = method_from('''
def get(self, request, slug):
    return DeployBoard.objects.filter(
        is_disabled=True,
        deleted_at__isnull=False,
        project__deleted_at__isnull=False,
        workspace__deleted_at__isnull=False,
        entity_name="private",
    )
''')
        self.assertEqual(CHECKS.keyword_names(method), set())

    def test_unrelated_orm_queries_cannot_satisfy_board_checks(self):
        method = method_from('''
def get(self, request, slug):
    Project.objects.filter(
        workspace__slug=slug, is_disabled=False,
        deleted_at__isnull=True, entity_name="project"
    )
    return DeployBoard.objects.filter(anchor=slug)
''')
        self.assertEqual(CHECKS.keyword_names(method), set())

    def test_wrong_identifiers_or_tenant_comparisons_fail_closed(self):
        method = method_from('''
def get(self, request, slug, project_id):
    return DeployBoard.objects.get(
        workspace__slug="some-other-workspace",
        project_id="another-project",
        entity_identifier=F("workspace_id"),
        project__workspace_id=F("project_id"),
    )
''')
        self.assertEqual(CHECKS.keyword_names(method), set())

    def test_unconditional_first_statement_denial_is_detected(self):
        method = method_from('''
def get(self, request, slug):
    raise NotFound()
''')
        self.assertTrue(CHECKS.unconditional_denial(method))

    def test_conditional_denial_is_not_accepted(self):
        method = method_from('''
def get(self, request, slug):
    if request.user.is_anonymous:
        raise NotFound()
    return DeployBoard.objects.all()
''')
        self.assertFalse(CHECKS.unconditional_denial(method))


if __name__ == "__main__":
    unittest.main()
