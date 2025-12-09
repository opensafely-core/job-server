import ast
import os

import psycopg2 as pg
import requests
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


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

# This query finds the project, workspace, and repo information for workspaces that have a job that ran in the last three months
open_project_query = """
        SELECT DISTINCT w.name AS "Workspace Name", p.id AS "Project ID", p.slug AS "Project Slug", p.status AS "Project Status", w.branch AS "Branch", r.url AS "Repo"
        FROM jobserver_workspace AS w
        INNER JOIN jobserver_project AS p ON (p.id = w.project_id)
        INNER JOIN jobserver_repo AS r ON (r.id = w.repo_id)
        INNER JOIN jobserver_jobrequest AS jr ON (w.id = jr.workspace_id)
        WHERE jr.created_at >= date_trunc('month', CURRENT_DATE - interval '3' MONTH)
        """


def read_data(query):
    # Use ReadDictCursor to return the result of the query as a dictionary
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query)
    project_info = cursor.fetchall()
    return project_info


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
    if response.status_code != 200:
        raise Exception(f"GitHub returned an error {response.status_code}")

    for branch in response.json():
        if branch["name"] == repo_branch:
            tree_sha = branch["commit"]["sha"]

    # return url for accessing trees endpoint
    tree_url = (
        f"https://api.github.com/repos/{org_repo}/git/trees/{tree_sha}?recursive=true"
    )
    return tree_url


def get_files_from_trees(repo_tree_url):
    response = requests.get(
        repo_tree_url,
        headers={"Authorization": f"token {SEARCH_API_TOKEN}"},
    )
    if response.status_code != 200:
        raise Exception(f"GitHub returned an error {response.status_code}")

    repo_py_scripts = [
        item["path"] for item in response.json()["tree"] if item["path"].endswith(".py")
    ]
    return repo_py_scripts


def get_tables_from_file_content(repo_url, repo_branch, python_files_in_repo):
    ehrql_tables = set()

    for file in python_files_in_repo:
        repo = get_org_repo_name(repo_url)
        branch = repo_branch
        file_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file}"

        response = requests.get(
            file_url, headers={"Authorization": f"token {SEARCH_API_TOKEN}"}
        )
        if response.status_code != 200:
            raise Exception(f"GitHub returned an error {response.status_code}")
        data = response.text

        ast_tree = ast.parse(data)

        tables = []
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.ImportFrom) and node.module == "ehrql.tables.tpp":
                tables.extend(alias.name for alias in node.names)

        for table in tables:
            ehrql_tables.add(table)

    if ehrql_tables:
        return ehrql_tables


def get_tables(repo_url, repo_branch):
    workspace_tree_url = get_branch_url(repo_url, repo_branch)
    python_files_in_repo = get_files_from_trees(workspace_tree_url)
    tpp_tables = get_tables_from_file_content(
        repo_url, repo_branch, python_files_in_repo
    )
    return tpp_tables


class Command(BaseCommand):
    def handle(self, *args, **options):
        def get_info_from_data():
            yield from read_data(open_project_query)

        project_dict = {}
        for i, project in enumerate(get_info_from_data()):
            repo_url = project["Repo"]
            repo_branch = project["Branch"]
            tables = get_tables(repo_url, repo_branch)

            project_tables = tables

            project_slug = project["Project Slug"]

            with open("project_tables_mapping.txt", "a") as f:
                f.write(
                    f"\n\n Round {i} before gouping: \n\n{project_slug}: {project_tables}"
                )

            existing_project = [
                item for item in project_dict.keys() if project_slug == item
            ]

            if project_tables and existing_project:
                merged_tables = project_dict[existing_project[0]] | project_tables
                project_dict[existing_project[0]] = merged_tables

            elif not project_tables and existing_project:
                with open("project_tables_mapping.txt", "a") as f:
                    f.write(
                        f"\n\nround {i} existing name but no tables: \n\n{project_dict}"
                    )
                continue
            else:
                project_dict[project_slug] = project_tables

            with open("project_tables_mapping.txt", "a") as f:
                f.write(f"\n\nround {i} after grouping: \n\n{project_dict}")

        with open("project_tables_mapping.txt", "a") as f:
            f.write(f"\n\nFull project-tables mapping: \n\n{project_dict}")
