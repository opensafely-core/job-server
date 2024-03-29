# Generated by Django 5.0.1 on 2024-01-09 10:21

from datetime import UTC, datetime

from django.db import migrations


data = [
    {"number": 1, "date": datetime(2021, 7, 15, tzinfo=UTC)},
    {"number": 2, "date": datetime(2021, 11, 10, tzinfo=UTC)},
    {"number": 3, "date": datetime(2021, 11, 10, tzinfo=UTC)},
    {"number": 4, "date": datetime(2021, 7, 15, tzinfo=UTC)},
    {"number": 8, "date": datetime(2021, 7, 15, tzinfo=UTC)},
    {"number": 9, "date": datetime(2021, 7, 15, tzinfo=UTC)},
    {"number": 11, "date": datetime(2021, 7, 15, tzinfo=UTC)},
    {"number": 13, "date": datetime(2021, 10, 27, tzinfo=UTC)},
    {"number": 14, "date": datetime(2021, 7, 15, tzinfo=UTC)},
    {"number": 15, "date": datetime(2021, 7, 15, tzinfo=UTC)},
    {"number": 17, "date": datetime(2021, 7, 15, tzinfo=UTC)},
    {"number": 20, "date": datetime(2021, 9, 21, tzinfo=UTC)},
    {"number": 21, "date": datetime(2021, 9, 28, tzinfo=UTC)},
    {"number": 26, "date": datetime(2021, 11, 17, tzinfo=UTC)},
    {"number": 27, "date": datetime(2022, 11, 23, tzinfo=UTC)},
    {"number": 28, "date": datetime(2021, 11, 23, tzinfo=UTC)},
    {"number": 30, "date": datetime(2021, 11, 24, tzinfo=UTC)},
    {"number": 31, "date": datetime(2021, 12, 8, tzinfo=UTC)},
    {"number": 33, "date": datetime(2021, 12, 16, tzinfo=UTC)},
    {"number": 34, "date": datetime(2021, 12, 20, tzinfo=UTC)},
    {"number": 35, "date": datetime(2021, 12, 15, tzinfo=UTC)},
    {"number": 36, "date": datetime(2021, 12, 15, tzinfo=UTC)},
    {"number": 37, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 41, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 43, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 44, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 45, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 48, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 49, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 50, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 51, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 52, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 53, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 55, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 56, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 58, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 59, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 60, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 61, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 62, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 63, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 65, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 66, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 67, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 72, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 74, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 76, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 79, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 80, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 81, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 82, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 84, "date": datetime(2020, 4, 6, tzinfo=UTC)},
    {"number": 93, "date": datetime(2022, 3, 9, tzinfo=UTC)},
    {"number": 111, "date": datetime(2022, 5, 6, tzinfo=UTC)},
]


def set_approval_dates(apps, schema_editor):
    Project = apps.get_model("jobserver", "Project")
    User = apps.get_model("jobserver", "User")

    for row in data:
        project = Project.objects.filter(number=row["number"]).first()

        if not project:  # we're not working with prod data
            continue

        assert project.applications.count() == 1
        application = project.applications.first()

        if not application.approved_by:
            application.approved_by = User.objects.get(username="ghickman")

        application.approved_at = row["date"]
        application.save(update_fields=["approved_at", "approved_by"])


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0010_jobrequest_codelists_ok"),
    ]

    operations = [
        migrations.RunPython(
            set_approval_dates,
            reverse_code=migrations.RunPython.noop,
        )
    ]
