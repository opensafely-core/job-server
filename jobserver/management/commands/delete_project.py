import sys

from django.core.management.base import BaseCommand

from jobserver.models import Project


def delete_project(name):
    project = Project.objects.get(name=name)
    if project.workspaces.exists() or project.members.exists():
        raise Exception("Unable to delete a project with workspaces or members")
    project.delete()
    print(f"Project {name} deleted")


class Command(BaseCommand):
    help = "Delete an empty project"  # noqa: A003

    def add_arguments(self, parser):
        parser.add_argument("project_name")

    def handle(self, *args, **options):
        project_name = options["project_name"]

        try:
            delete_project(project_name)
        except Project.DoesNotExist:
            sys.exit("Project does not exist")
        except Exception as e:
            sys.exit(str(e))
