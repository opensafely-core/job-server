import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from furl import furl

from jobserver.models import Project, Workspace


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("project")
        parser.add_argument("workspace")

    def handle(self, *args, **options):
        project_slug = options["project"]
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            self.stderr.write(f"Unknown Project slug: {project_slug}")
            sys.exit(1)

        workspace_name = options["workspace"]
        try:
            workspace = Workspace.objects.get(name=workspace_name)
        except Project.DoesNotExist:
            self.stderr.write(f"Unknown Workspace name: {workspace_name}")
            sys.exit(1)

        workspace.project = project
        workspace.save()

        # tell the User where they can view the Workspace now
        f = furl(settings.BASE_URL)
        f.path = project.get_absolute_url()
        self.stdout.write(f"Project: {f.url}")
