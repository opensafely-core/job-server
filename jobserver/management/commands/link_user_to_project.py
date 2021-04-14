import sys

from django.core.management.base import BaseCommand

from jobserver.authorization import strings_to_roles
from jobserver.models import Project, ProjectMembership, User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("project")
        parser.add_argument("roles", nargs="+")

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(f"Unknown username: {username}")

        project_slug = options["project"]
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            self.stderr.write(f"Unknown Project slug: {project_slug}")
            sys.exit(1)

        try:
            selected_roles = strings_to_roles(
                options["roles"], "jobserver.models.ProjectMembership"
            )
        except Exception as e:
            self.stderr.write(str(e))
            sys.exit(1)

        ProjectMembership.objects.create(
            project=project, user=user, roles=selected_roles
        )
