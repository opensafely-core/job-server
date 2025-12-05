import re
from datetime import timedelta

import requests
import yaml
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
                workspace.branch,
            ]
            for i, workspace in enumerate(workspace_projects)
        ]
        headers = ["S/N", "Project", "Project Status", "Workspace", "Repo", "Branch"]
        table = tabulate(
            project_workspace_repo,
            headers=headers,
            tablefmt="grid",
            maxcolwidths=[None, 30, None, 30, 30, None],
        )

        # Display open projects in console
        print(table)

        # TODO: Write a script that can query the repo for information on the tables that are used in the ehrQL code
        # This will use the github API

        # Get the actual file using githubusercontent and not the html github page of the file
        base_url = "https://raw.githubusercontent.com/opensafely/post-covid-renal/main/project.yaml"  # hardcoded example
        response = requests.get(base_url)

        yaml_file = response.text

        # Parse the yaml file into a python dictionary
        yaml_dict = yaml.safe_load(yaml_file)

        # Get the paths to the dataset definition in repos
        dataset_definition = []
        for _, value in yaml_dict["actions"].items():
            data_string = str(value)
            for item in data_string.split():
                if ".py" in item:
                    dataset_definition.append(item)
        print(dataset_definition)

        # Query the dataset definition files for ehrql tpp tables using regex
        ehrql_tables = ""
        for file in dataset_definition:
            file_url = f"https://raw.githubusercontent.com/opensafely/post-covid-renal/main/{file}"
            response = requests.get(file_url)
            data = response.text

            pattern = r"from ehrql.tables.tpp import \(?([\w, \n]+)"
            imports = re.findall(pattern, data)

            for i, item in enumerate(imports):
                table_data = item.strip()
                ehrql_tables += table_data

                if i < (len(imports) - 1):
                    ehrql_tables += ", "

        print(ehrql_tables)
