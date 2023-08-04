import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from furl import furl

from jobserver import commands, models


def get_org(pk: int) -> models.Org:
    org_lut = {
        1: "datalab",  # bennett
        2: "university-of-surrey",  # surry
        3: "kings-college-london",  # kings
    }
    return models.Org.objects.get(slug=org_lut[pk])


def get_user(pk: int) -> models.User:
    user_lut = {
        1: "rebkwok",  # becky.smith@thedatalab.org
        2: "tomodwyer",  # tom.odwyer@thedatalab.org
        3: "benbc",  # ben.butler-cole@thedatalab.org
        7: "LFISHER7",  # louis.fisher@thedatalab.org
        10: "iaindillingham",  # iain.dillingham@thedatalab.org
        11: "HelenCEBM",  # helen.curtis@thedatalab.org
        12: "wjchulme",  # william@thedatalab.org
        14: "andrewscolm",  # colm.andrews@thedatalab.org
        18: "LisaHopcroft",  # lisa.hopcroft@thedatalab.org
        20: "ccunningham101",  # christine.cunningham@thedatalab.org
        21: "rose-higgins",  # rose.higgins@thedatalab.org
        29: "LindaNab",  # linda.nab@thedatalab.org
        31: "lemanska",  # a.lemanska@surrey.ac.uk
        32: "markdrussell",  # mark.russell@kcl.ac.uk
    }
    return models.User.objects.get(username=user_lut[pk])


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument(
        #     "user_mapping",
        #     type=Path,
        #     help="Path to file mapping reports users to job-server users",
        # )
        parser.add_argument(
            "data",
            type=Path,
            help="Path to file mapping reports users to job-server users",
        )

    @transaction.atomic()
    def handle(self, *args, **options):
        path = options["data"]

        with path.open() as f:
            data = json.load(f)

        # orgs = [get_org(o["pk"]) for o in data if o["model"] == "reports.org"]
        # print(len(orgs))
        # users = [u for u in data if u["model"] == "gateway.user"]
        # print(len(users))
        reports = [r["fields"] for r in data if r["model"] == "reports.report"]
        print(f"Total reports: {len(reports)}")
        print("")

        print("Reports hosted on GitHub:")
        for r in sorted(
            (r for r in reports if not r["job_server_url"]), key=lambda r: r["title"]
        ):
            print(f" - {r['title']}")
        print("")

        job_server_reports = [r for r in reports if r["job_server_url"]]
        for data in job_server_reports:
            f = furl(data["job_server_url"].rstrip("/"))
            rfile = models.ReleaseFile.objects.get(pk=f.path.segments[-1])
            user = get_user(data["created_by"])
            report = commands.create_report(
                rfile=rfile,
                title=data["title"],
                description=data["description"],
                user=user,
            )
            updater = get_user(data["updated_by"])

            # update audit fields
            report.updated_by = updater
            report.created_at = data["created_at"]
            report.updated_at = data["updated_at"]
            report.save()

            if data["is_draft"] is False:
                models.PublishRequest.create_from_report(
                    report=report, user=updater
                ).approve(user=updater)
            assert report.is_draft == data["is_draft"]

        print(f"Would add {len(job_server_reports)} reports")
        raise CommandError("Exiting to avoid committing this transaction")
