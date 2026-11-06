# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Synthetic SQLite checks of the actual migration; does not load Plane services."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / 'apps/api/plane/license/migrations/0007_default_telemetry_opt_out.py'


@unittest.skipUnless(importlib.util.find_spec('django') is not None, 'Django not installed')
class TelemetryMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[],
                DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
                DEFAULT_AUTO_FIELD='django.db.models.AutoField',
                SECRET_KEY='isolated-migration-test-only',
            )
        import django
        django.setup()

    def test_forward_and_reverse_preserve_existing_preferences(self):
        from django.db import models
        from django.db.migrations.state import ModelState, ProjectState
        from django.db.utils import ConnectionHandler

        spec = importlib.util.spec_from_file_location('gc_telemetry_migration', MIGRATION)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        migration = module.Migration('0007_default_telemetry_opt_out', 'license')
        self.assertEqual(migration.dependencies, [('license', '0006_instance_is_current_version_deprecated')])
        self.assertEqual(len(migration.operations), 1)
        operation = migration.operations[0]

        old = ProjectState()
        old.add_model(ModelState(
            'license', 'Instance',
            [
                ('id', models.AutoField(primary_key=True)),
                ('is_telemetry_enabled', models.BooleanField(default=True)),
            ],
            options={'db_table': 'instances'},
        ))
        connection = ConnectionHandler({
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        })['default']
        try:
            old_model = old.apps.get_model('license', 'Instance')
            with connection.schema_editor() as editor:
                editor.create_model(old_model)
            old_model.objects.using(connection.alias).create(id=1, is_telemetry_enabled=True)
            old_model.objects.using(connection.alias).create(id=2, is_telemetry_enabled=False)

            new = old.clone()
            operation.state_forwards('license', new)
            with connection.schema_editor() as editor:
                operation.database_forwards('license', editor, old, new)
            new_model = new.apps.get_model('license', 'Instance')
            self.assertIs(new_model._meta.get_field('is_telemetry_enabled').default, False)
            self.assertEqual(
                list(new_model.objects.using(connection.alias).order_by('id').values_list('id', 'is_telemetry_enabled')),
                [(1, True), (2, False)],
            )
            new_model.objects.using(connection.alias).create(id=3)
            self.assertFalse(new_model.objects.using(connection.alias).get(id=3).is_telemetry_enabled)

            with connection.schema_editor() as editor:
                operation.database_backwards('license', editor, new, old)
            old_model = old.apps.get_model('license', 'Instance')
            self.assertIs(old_model._meta.get_field('is_telemetry_enabled').default, True)
            self.assertEqual(
                list(old_model.objects.using(connection.alias).order_by('id').values_list('id', 'is_telemetry_enabled')),
                [(1, True), (2, False), (3, False)],
            )
        finally:
            connection.close()


if __name__ == '__main__':
    unittest.main()
