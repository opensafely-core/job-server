from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from tabulate import tabulate

from jobserver.models import Project, Workspace


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Get open projects using metrics in sync with grafana database: open projects are those which have had a job request created within the last three months
        three_months_ago = timezone.now() - timedelta(days=30 * 3)

        # A project can have multiple job requests, so calling distinct() in this query displays the unique projects
        open_projects = Project.objects.filter(
            workspaces__job_requests__created_at__gte=three_months_ago
        ).distinct()

        workspace_projects = Workspace.objects.filter(project__in=open_projects)

        project_workspace_repo = [
            [
                i + 1,
                workspace.project,
                workspace.project.status,
                workspace.name,
                workspace.repo,
            ]
            for i, workspace in enumerate(workspace_projects)
        ]
        headers = ["S/N", "Project", "Project Status", "Workspace", "Repo"]
        table = tabulate(
            project_workspace_repo,
            headers=headers,
            tablefmt="grid",
            maxcolwidths=[None, 30, None, 30, 30],
        )
        print(table)
