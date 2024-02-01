import sys

from django.core.management.base import BaseCommand
from django.db import transaction

from jobserver.models import Org, Project, ProjectCollaboration, User


class MergeException(Exception):
    pass


@transaction.atomic()
def merge_projects(username, primary_slug, other_slugs):
    try:
        operator = User.objects.get(username=username)
    except User.DoesNotExist:
        raise MergeException("User does not exist")

    try:
        primary = Project.objects.get(slug=primary_slug)
    except Project.DoesNotExist:
        raise MergeException("Primary project does not exist")

    others = Project.objects.filter(slug__in=other_slugs)

    if missing := set(other_slugs) - set(others.values_list("slug", flat=True)):
        raise MergeException(f"Unknown projects: {', '.join(missing)}")

    other_names = list(others.values_list("name", flat=True))

    # preserve any orgs not already on the primary
    orgs = Org.objects.filter(projects__in=others).exclude(projects=primary).distinct()
    for org in orgs:
        ProjectCollaboration.objects.create(
            project=primary,
            org=org,
            created_by=operator,
            updated_by=operator,
        )

    for project in others:
        # set up redirect
        primary.redirects.create(
            created_by=operator,
            old_url=project.get_absolute_url(),
        )

        # move workspaces
        project.workspaces.update(project=primary)

        # move members which are not already in the project to the primary project
        project.memberships.exclude(
            user__username__in=primary.members.values_list("username")
        ).update(project=primary)

        project.collaborations.all().delete()

    others.delete()

    name_list = "\n - ".join(other_names)
    print(f"Projects deleted:\n{name_list}")


class Command(BaseCommand):  # pragma: no cover
    help = "Merge the given projects into the given primary project"  # noqa: A003

    def add_arguments(self, parser):
        parser.add_argument(
            "username",
            help="Your username on GitHub, to create redirects with.",
        )
        parser.add_argument(
            "primary_project",
            help="The project to move all objects to.",
        )
        parser.add_argument(
            "other_projects",
            nargs="+",
            help="The projects whose objects will be merged to the primary project.",
        )

    def handle(self, *args, **options):
        username = options["username"]
        primary = options["primary_project"]
        others = options["other_projects"]

        try:
            merge_projects(username, primary, others)
        except Exception as e:
            sys.exit(str(e))
