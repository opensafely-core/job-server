import csv

from django.core.management.base import BaseCommand
from django.db import transaction

from jobserver.authorization import ProjectCoordinator, ProjectDeveloper
from jobserver.models import (
    Org,
    OrgMembership,
    Project,
    ProjectMembership,
    User,
    Workspace,
)


class Command(BaseCommand):
    @transaction.atomic()
    def handle(self, *args, **options):
        with open("project-mappings.csv") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            org, _ = Org.objects.get_or_create(slug=row["org_slug"])
            project, _ = Project.objects.get_or_create(
                org=org, name=row["project_name"]
            )

            try:
                coordinator = User.objects.get(username=row["coordinator"])
            except User.DoesNotExist:
                print(f"Unknown user: {row['coordinator']}")
                raise

            ProjectMembership.objects.create(
                project=project, user=coordinator, roles=[ProjectCoordinator]
            )

            usernames = [u for u in row["members"].split(",") if u]
            for username in usernames:
                user = User.objects.get(username=username)
                ProjectMembership.objects.create(
                    project=project, user=user, roles=[ProjectDeveloper]
                )

            org_members = [coordinator, *usernames]
            for member in org_members:
                user = User.objects.get(username=member)
                OrgMembership.objects.get_or_create(user=user, org=org)

            names = [n for n in row["workspaces"].split(",") if n]
            for name in names:
                workspace = Workspace.objects.get(name=name)
                workspace.project = project
                workspace.save()
