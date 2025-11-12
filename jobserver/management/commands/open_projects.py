from django.core.management.base import BaseCommand
from django.db.models import Q

from jobserver.models import Project


class Command(BaseCommand):
    def handle(self, *args, **options):
        open_projects = Project.objects.filter(
            Q(status=Project.Statuses.ONGOING)
            | Q(status=Project.Statuses.ONGOING_LINKED)
        )
        open_project_list = [
            f"{project.name} - {project.status}" for project in open_projects
        ]

        print(open_project_list)
