"""Management command to update the status of a RAP's Jobs via the RAP API."""

import structlog
from django.core.management.base import BaseCommand

from jobserver import rap_api

from ...models import Job


logger = structlog.get_logger(__name__)

COMPLETED_STATES = {"failed", "succeeded"}


class Command(BaseCommand):
    """Management command to update the status of a RAP's Jobs via the RAP API."""

    help = "Update RAP's jobs status via the RAP API."

    def add_arguments(self, parser):
        parser.add_argument(
            "rap_ids",
            nargs="+",
            type=str,
            help="IDs of the RAPs to update.",
        )

    def handle(self, *args, **options):
        try:
            json_response = rap_api.status(
                options["rap_ids"],
            )

            for job_from_api in json_response["jobs"]:
                logger.info(
                    f"RAP: {job_from_api['rap_id']} Job: {job_from_api['identifier']} Status: {job_from_api['status']}"
                )
                # TODO: this does not create any unexpected jobs
                job_from_db = Job.objects.get(
                    identifier=job_from_api["identifier"],
                )
                # TODO: better verification check?
                assert job_from_db.job_request.identifier == job_from_api["rap_id"]

                # COPY PASTA FROM api/jobs.py
                newly_completed = (
                    job_from_db.status not in COMPLETED_STATES
                    and job_from_api["status"] in COMPLETED_STATES
                )

                # update Job "manually" so we can make the check above for
                # status transition
                for key, value in job_from_api.items():
                    setattr(job_from_db, key, value)

                # TODO: commented out for testing!
                job_from_db.save()

                if newly_completed:
                    logger.info(f"{job_from_db.identifier} newly completed")

            for unrecognised_rap_id in json_response["unrecognised_rap_ids"]:
                logger.info(f"Unrecognised RAP id: {unrecognised_rap_id}")

        except Exception as exc:
            logger.error(exc)
