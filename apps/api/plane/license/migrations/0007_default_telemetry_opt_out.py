# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
"""Change new instance telemetry default without modifying existing preferences."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("license", "0006_instance_is_current_version_deprecated"),
    ]

    operations = [
        migrations.AlterField(
            model_name="instance",
            name="is_telemetry_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
