import psycopg2 as pg
from django.core.management.base import BaseCommand
from psycopg2.extras import RealDictCursor
from tabulate import tabulate


HOSTNAME = "localhost"
DATABASE = "jobserver"
USERNAME = "user"
PASSWORD = "pass"
PORT = "6543"

conn = pg.connect(
    host=HOSTNAME, user=USERNAME, password=PASSWORD, dbname=DATABASE, port=PORT
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        open_project_query = """
        SELECT p."id" AS "Project ID", p."name" AS "Project name", p."status" AS "Project Status", w."name" AS "Workspace name", w."branch" AS "Branch", r."url" AS "Repo"
        FROM "jobserver_workspace" AS w
        INNER JOIN "jobserver_project" AS p ON (p."id" = w."project_id")
        LEFT JOIN "jobserver_repo" AS r ON (r."id" = w."repo_id")
        WHERE w."project_id"
        IN (SELECT DISTINCT U0."id" FROM "jobserver_project" U0 INNER JOIN "jobserver_workspace" U1 ON (U0."id" = U1."project_id")
        INNER JOIN "jobserver_jobrequest" U2 ON (U1."id" = U2."workspace_id")
        WHERE U2."created_at" >= date_trunc('month', current_date - interval '3' month))
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
