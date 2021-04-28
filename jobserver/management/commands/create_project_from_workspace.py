import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from furl import furl

from jobserver.models import Org, Project, Workspace


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("org")
        parser.add_argument("--project")
        parser.add_argument("workspace")

    def _create_project(self, *, org, workspace):
        """Create a Project for the given Workspace in the given Org"""

        # remove common branch names
        slug = (
            workspace.name.removesuffix("-main")
            .removesuffix("_main")
            .removesuffix("-master")
            .removesuffix("_master")
        )

        # generate a name from the slug
        name = " ".join(word.capitalize() for word in slug.split("-"))

        project, _ = Project.objects.get_or_create(org=org, name=name, slug=slug)

        # tell the User what was made and where they can view it
        f = furl(settings.BASE_URL)
        f.path = project.get_absolute_url()
        self.stdout.write(f"Name: {project.name}\nURL:  {f.url}")

        return project

    def handle(self, *args, **options):
        org_slug = options["org"]
        try:
            org = Org.objects.get(slug=org_slug)
        except Org.DoesNotExist:
            self.stderr.write(f"Unknown Org slug: {org_slug}")
            sys.exit(1)

        workspace_slug = options["workspace"]
        try:
            workspace = Workspace.objects.get(name=workspace_slug)
        except Workspace.DoesNotExist:
            self.stderr.write(f"Unknown Workspace slug: {workspace_slug}")
            sys.exit(1)

        project_slug = options["project"]
        if project_slug:
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                self.stderr.write(f"Unknown Project slug: {project_slug}")
                sys.exit(1)
        else:
            project = self._create_project(org=org, workspace=workspace)

        workspace.project = project
        workspace.save()
