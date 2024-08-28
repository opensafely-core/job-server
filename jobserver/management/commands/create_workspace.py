from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from jobserver.authorization.roles import (
    ProjectCollaborator,
    ProjectDeveloper,
)
from jobserver.commands import project_members
from jobserver.models import Project, Repo, User, Workspace


class Command(BaseCommand):
    """
    Create or update a workspace.

    Will create Project and Repo as needed, and ensure the supplied user as
    Project Developer of the workspace.
    """

    def add_arguments(self, parser):
        parser.add_argument("workspace", help="Workspace name")
        parser.add_argument(
            "username",
            help="User to create workspaced with and add to workspace permissions",
        )
        parser.add_argument(
            "--project", default=None, help="project name (defaults to workspace name)"
        )
        parser.add_argument(
            "--repo", default=None, help="repo url (defaults to /org/$workspace)"
        )

    @transaction.atomic()
    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError(
                f"Cannot find user {options['username']}. Maybe you need to run create_user first?"
            )

        project_slug = options["project"] or options["workspace"]

        project_values = {
            "name": project_slug,
            "created_by": user,
            "updated_by": user,
        }

        project, created = Project.objects.update_or_create(
            slug=project_slug, defaults=project_values
        )

        self.stdout.write(
            f"{'Created' if created else 'Updated'} project {project.slug}"
        )

        repo, _ = Repo.objects.get_or_create(
            url=options["repo"] or f"/org/{options['workspace']}"
        )

        workspace_values = {
            "name": options["workspace"],
            "created_by": user,
            "updated_by": user,
            "repo": repo,
            "project": project,
        }

        workspace, created = Workspace.objects.update_or_create(
            name=options["workspace"], defaults=workspace_values
        )
        self.stdout.write(
            f"{'Created' if created else 'Updated'} workspace {workspace.name}"
        )

        if user not in project.members.all():
            project_members.add(
                project=project,
                user=user,
                roles=[ProjectDeveloper, ProjectCollaborator],
                by=user,
            )
            self.stdout.write(
                f"Added {user.username} to workspace {workspace.name} as ProjectDeveloper and ProjectCollaborator"
            )
