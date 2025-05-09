# Generated by Django 5.1.6 on 2025-03-20 09:36
# Then manually edited to remove the vestigal dependency on the interactive
# app migrations which are planned for removal.

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import redirects.models


class Migration(migrations.Migration):
    replaces = [
        ("redirects", "0001_initial"),
        ("redirects", "0002_ensure_old_url_has_leading_and_trailing_slashes"),
        (
            "redirects",
            "0003_remove_redirect_redirects_redirect_only_one_target_model_set_and_more",
        ),
    ]

    dependencies = [
        ("jobserver", "0001_squashed_2024_06"),
        ("jobserver", "0011_sitealert"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Redirect",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("old_url", models.TextField(db_index=True)),
                (
                    "expires_at",
                    models.DateTimeField(default=redirects.models.default_expires_at),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="redirects_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="redirect_deleted",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="redirects",
                        to="jobserver.org",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="redirects",
                        to="jobserver.project",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="redirects",
                        to="jobserver.workspace",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(
                                ("deleted_at__isnull", True),
                                ("deleted_by__isnull", True),
                            ),
                            models.Q(
                                ("deleted_at__isnull", False),
                                ("deleted_by__isnull", False),
                            ),
                            _connector="OR",
                        ),
                        name="redirects_redirect_both_deleted_at_and_deleted_by_set",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("old_url", ""), _negated=True),
                        name="old_url_is_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("old_url__endswith", "/"), ("old_url__startswith", "/")
                        ),
                        name="old_url_endswith_and_startswith_slash",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(
                                ("org__isnull", False),
                                ("project__isnull", True),
                                ("workspace__isnull", True),
                            ),
                            models.Q(
                                ("org__isnull", True),
                                ("project__isnull", False),
                                ("workspace__isnull", True),
                            ),
                            models.Q(
                                ("org__isnull", True),
                                ("project__isnull", True),
                                ("workspace__isnull", False),
                            ),
                            _connector="OR",
                        ),
                        name="redirects_redirect_only_one_target_model_set",
                    ),
                ],
            },
        ),
    ]
