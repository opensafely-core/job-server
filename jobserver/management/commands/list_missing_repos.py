import csv
import re

from attrs import define
from django.core.management.base import BaseCommand

from jobserver.models import Repo


url_pat = re.compile(r".*(?P<url>https://github.com/opensafely/.*)[/]?")


@define
class Data:
    number: int
    url: str


def get_url(s):
    """Search for a GitHub URL in the given string"""
    m = url_pat.search(s)

    return m.group("url") if m else ""


class Command(BaseCommand):
    """
    A command to search for projects with repos we don't know about

    As part of Team IG's audit of the job-server data they have produced a
    spreadsheet with project number and repo URLs (among other things).  We
    know some of those repos are unknown to job-server, because they predate
    it.

    This command finds those repo URLs in the data and looks up which ones
    job-server does not know about.

    Team IG can provide you a link to the spreadsheet if you need it.  Export
    it to a CSV and then run this command to find which repos are unknown.
    """

    def add_arguments(self, parser):
        parser.add_argument("csv", help="CSV to parse for repos")

    def handle(self, *args, **options):
        with open(options["csv"]) as f:
            rows = list(csv.reader(f))

        # ditch the first few rows as they're docs and a scratch pad
        rows = rows[4:]

        projects = [Data(number=row[0], url=get_url(row[5])) for row in rows]

        for project in projects:
            if not project.url:
                continue

            # break down into just the name in case that's a better substring
            # than the full URL
            _, _, name = project.url.rstrip("/").rpartition("/")
            try:
                Repo.objects.get(url__icontains=name)
            except (Repo.DoesNotExist, Repo.MultipleObjectsReturned):
                print(project.number, project.url)
