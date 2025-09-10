"""Management command to update the status of a RAP's Jobs via the RAP API."""

import structlog
from django.core.management.base import BaseCommand

from jobserver import rap_api
from jobserver.models import JobRequest


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
            job_requests = JobRequest.objects.filter(identifier__in=options["rap_ids"])
            job_request_lut = {jr.identifier: jr for jr in job_requests}

            created_job_ids = []
            updated_job_ids = []
            deleted_identifiers = []

            for rap_id in options["rap_ids"]:
                # TODO: move this out of the management command!!

                if rap_id in json_response["unrecognised_rap_ids"]:
                    continue

                # get the JobRequest for this identifier
                job_request = job_request_lut.get(rap_id)

                # This could happen if the management command is given a rap_id which
                # does not exist on job-server but does exist on the controller.
                if job_request is None:
                    logger.info(f"Job-server does not recognise RAP id: {rap_id}")
                    continue

                # bind the job request ID to further logs so looking them up
                # in the UI is easier
                structlog.contextvars.bind_contextvars(job_request=job_request.id)

                jobs_from_api = [
                    j for j in json_response["jobs"] if j.get("rap_id") == rap_id
                ]

                database_jobs = job_request.jobs.all()

                # get the current Jobs for the JobRequest, keyed on their identifier
                jobs_by_identifier = {j.identifier: j for j in database_jobs}

                payload_identifiers = {j["identifier"] for j in jobs_from_api}

                # delete local jobs not in the payload
                identifiers_to_delete = (
                    set(jobs_by_identifier.keys()) - payload_identifiers
                )
                if identifiers_to_delete:
                    job_request.jobs.filter(
                        identifier__in=identifiers_to_delete
                    ).delete()
                    for identifier in identifiers_to_delete:
                        deleted_identifiers.append(str(identifier))

                for job_from_api in jobs_from_api:
                    logger.info(
                        f"RAP: {job_from_api['rap_id']} Job: {job_from_api['identifier']} Status: {job_from_api['status']}"
                    )

                    # Remove rap_id from the data, it's going to be set by
                    # creating/updating Job instances via the JobRequest instances
                    # related Jobs manager (ie job_request.jobs)
                    # Also remove some other values which we don't currently store in Job
                    superfluous_keys = ["rap_id", "backend", "requires_db"]

                    for superfluous_key in superfluous_keys:
                        job_from_api.pop(superfluous_key, None)

                    job_from_db, created = job_request.jobs.get_or_create(
                        identifier=job_from_api["identifier"],
                        defaults={**job_from_api},
                    )

                    if created:
                        created_job_ids.append(str(job_from_db.id))
                        # For newly created jobs we can't tell if they've just
                        # transitioned to completed so we assume they have to avoid
                        # missing notifications
                        newly_completed = job_from_db.status in COMPLETED_STATES
                    else:
                        updated_job_ids.append(str(job_from_db.id))

                        newly_completed = (
                            job_from_db.status not in COMPLETED_STATES
                            and job_from_api["status"] in COMPLETED_STATES
                        )

                        # update Job "manually" so we can make the check above for
                        # status transition
                        for key, value in job_from_api.items():
                            setattr(job_from_db, key, value)

                    job_from_db.save()

                    if newly_completed:
                        job_from_db.refresh_from_db()
                        logger.info(f"{job_from_db.identifier} newly completed")
                        # TODO: port this to here!
                        # handle_job_notifications(job_request, job_from_db)

            # TODO: should we log ids or identifiers here? ids are not so helpful
            logger.info(
                "Created, updated or deleted Jobs",
                created_job_ids=",".join(created_job_ids),
                updated_job_ids=",".join(updated_job_ids),
                deleted_job_identifiers=",".join(deleted_identifiers),
            )
            if json_response["unrecognised_rap_ids"]:
                logger.info(
                    f"Unrecognised RAP ids: {','.join(json_response['unrecognised_rap_ids'])}"
                )

        except Exception as exc:
            logger.error(exc)
