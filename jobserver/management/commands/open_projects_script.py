import os
import re

import psycopg2 as pg
import requests
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from tabulate import tabulate


# TODO: Write a just recipe which will get the latest jobserver.dump every tiime the script is run and the run just docker/restore-db so it rebuilds the docker container with the latest db

# TODO: move these to a .env file in new repo
HOSTNAME = "localhost"
DATABASE = "jobserver"
USERNAME = "user"
PASSWORD = "pass"
PORT = "6543"

load_dotenv()
SEARCH_API_TOKEN = os.getenv("SEARCH_API_TOKEN")

conn = pg.connect(
    host=HOSTNAME, user=USERNAME, password=PASSWORD, dbname=DATABASE, port=PORT
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        # This query finds the project, workspace, and repo information for workspaces that have a job that ran in the last three months
        open_project_query = """
        SELECT DISTINCT w.name AS workspace_name, p."id" AS "Project ID", p."name" AS "Project name", p."status" AS "Project Status", w."branch" AS "Branch", r."url" AS "Repo"
        FROM jobserver_workspace AS w
        INNER JOIN jobserver_project AS p ON (p.id = w.project_id)
        INNER JOIN jobserver_repo AS r ON (r.id = w.repo_id)
        INNER JOIN jobserver_jobrequest AS jr ON (w.id = jr.workspace_id)
        WHERE jr.created_at >= date_trunc('month', CURRENT_DATE - interval '3' MONTH)
        """

        def read_data():
            # Use ReadDictCursor to return the result of the query as a dictionary
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(open_project_query)
            project_info = cursor.fetchall()
            return project_info

        def display_table():
            table_rows = read_data()
            table = tabulate(
                table_rows,
                headers="keys",
                tablefmt="grid",
                maxcolwidths=[None, 60, 30, None, 30, 15, 15],
                showindex="always",
            )
            return table

        print(display_table())

        def get_info_from_data():
            yield from read_data()

        def get_org_repo_name(repo_url) -> str:
            url_segments = repo_url.split("/")
            repo_name = "/".join(url_segments[3:])
            return repo_name

        def get_branch_url(repo_url, repo_branch):
            org_repo = get_org_repo_name(repo_url)

            # Use branches endpoint to get all the branches in the repo
            url = f"https://api.github.com/repos/{org_repo}/branches"
            response = requests.get(
                url,
                headers={"Authorization": f"token {SEARCH_API_TOKEN}"},
            )

            for branch in response.json():
                if branch["name"] == repo_branch:
                    tree_sha = branch["commit"]["sha"]

            # return url for accessing trees endpoint
            tree_url = f"https://api.github.com/repos/{org_repo}/git/trees/{tree_sha}?recursive=true"
            return tree_url

        def get_file_from_trees(repo_tree_url):
            # repo_tree_url = get_branch_url()
            response = requests.get(
                repo_tree_url,
                headers={"Authorization": f"token {SEARCH_API_TOKEN}"},
            )
            for item in response.json()["tree"]:
                if ".py" in item["path"]:
                    pass
            repo_py_scripts = [
                item["path"]
                for item in response.json()["tree"]
                if ".py" in item["path"]
            ]
            return repo_py_scripts

        def get_table_from_file_content(repo_url, python_files_in_repo):
            # python_files_in_repo = get_file_from_trees()

            ehrql_tables = set()
            for file in python_files_in_repo:
                repo = get_org_repo_name(repo_url)
                branch = "main"
                file_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file}"
                response = requests.get(file_url)
                data = response.text

                pattern = r"from ehrql.tables.tpp import \(?([\w, \n]+)"
                imports = re.findall(pattern, data)

                for item in imports:
                    tables = [t.strip() for t in item.split(",") if t.strip()]
                    for table in tables:
                        ehrql_tables.add(table)

            # TODO: add an extra column & key to display_table() and read_data() respectively called "tpp tables"
            return ehrql_tables

        for project in get_info_from_data():
            repo_url = project["Repo"]
            repo_branch = project["Branch"]

            workspace_tree_url = get_branch_url(repo_url, repo_branch)
            python_files_in_repo = get_file_from_trees(workspace_tree_url)
            tpp_tables = get_table_from_file_content(repo_url, python_files_in_repo)

            print(f"Repo:\n{repo_url}\nTpp tables:\n{tpp_tables}\n\n")
