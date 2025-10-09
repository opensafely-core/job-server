import datetime

import structlog
from django.db.models import Q
from django.utils import timezone

from jobserver import rap_api
from jobserver.models import Job, JobRequest
from jobserver.models.job import COMPLETED_STATES


logger = structlog.get_logger(__name__)


def get_active_job_request_ids():
    active_job_jobrequest_ids = (
        Job.objects.filter(status__in=["pending", "running"])
        .values_list("job_request_id")
        .distinct()
    )
    # For interim RAP API s2 work, this only finds Jobs/JobRequests for the test backend
    # We also filter JobRequests that we identify by their _status field to only those created within the
    # past 365 days, to avoid returning any very old job requests that may have unknown status due to
    # historical differences in the way the job status field was set.
    one_year_ago = timezone.now() - datetime.timedelta(weeks=52)
    active_job_requests = JobRequest.objects.filter(
        Q(
            _status__in=["pending", "running", "unknown"],
            created_at__gte=one_year_ago,
            backend__slug="test",
        )
        | Q(id__in=active_job_jobrequest_ids)
    )
    return [jr.identifier for jr in active_job_requests]


def rap_status_update(rap_ids):
    json_response = rap_api.status(
        rap_ids,
    )
    job_requests = JobRequest.objects.filter(identifier__in=rap_ids).prefetch_related(
        "jobs"
    )
    job_request_by_identifier = {jr.identifier: jr for jr in job_requests}

    created_job_ids = []
    created_job_identifiers = []
    updated_job_ids = []
    updated_job_identifiers = []
    deleted_identifiers = []

    # Remove rap_id from the data, it's going to be set by
    # creating/updating Job instances via the JobRequest instances
    # related Jobs manager (ie job_request.jobs)
    # Also remove some other values which we don't currently store in Job
    superfluous_job_keys = ["rap_id", "backend", "requires_db"]

    for rap_id in rap_ids:
        if rap_id in json_response["unrecognised_rap_ids"]:
            continue

        job_request = job_request_by_identifier.get(rap_id)

        # This could happen if the management command is given a rap_id which
        # does not exist on job-server but does exist on the controller.
        if job_request is None:
            logger.warning(f"Job-server does not recognise RAP id: {rap_id}")
            continue

        # bind the job request ID to further logs so looking them up
        # in the UI is easier
        with structlog.contextvars.bound_contextvars(job_request=job_request.id):
            jobs_from_api = [
                j for j in json_response["jobs"] if j.get("rap_id") == rap_id
            ]

            database_jobs = job_request.jobs.all()

            # get the current Jobs for the JobRequest, keyed on their identifier
            jobs_by_identifier = {j.identifier: j for j in database_jobs}

            payload_identifiers = {j["identifier"] for j in jobs_from_api}

            # delete local jobs not in the payload
            identifiers_to_delete = set(jobs_by_identifier.keys()) - payload_identifiers
            if identifiers_to_delete:
                job_request.jobs.filter(identifier__in=identifiers_to_delete).delete()
                for identifier in identifiers_to_delete:
                    deleted_identifiers.append(str(identifier))

            for job_from_api in jobs_from_api:
                logger.info(
                    f"RAP: {job_from_api['rap_id']} Job: {job_from_api['identifier']} Status: {job_from_api['status']}"
                )

                for superfluous_key in superfluous_job_keys:
                    job_from_api.pop(superfluous_key, None)

                job_from_db, created = job_request.jobs.get_or_create(
                    identifier=job_from_api["identifier"],
                    defaults={**job_from_api},
                )
                assert isinstance(job_from_db, Job)

                if created:
                    created_job_ids.append(str(job_from_db.id))
                    created_job_identifiers.append(str(job_from_db.identifier))
                    # For newly created jobs we can't tell if they've just
                    # transitioned to completed so we assume they have to avoid
                    # missing notifications
                    newly_completed = job_from_db.is_completed
                else:
                    updated_job_ids.append(str(job_from_db.id))
                    updated_job_identifiers.append(str(job_from_db.identifier))

                    newly_completed = (
                        not job_from_db.is_completed
                        and job_from_api["status"] in COMPLETED_STATES
                    )

                    # Update the Job here rather than using create_or_update above, as
                    # we needed to check the pre-update status to identify newly
                    # created jobs.
                    for key, value in job_from_api.items():
                        setattr(job_from_db, key, value)

                # TODO: use bulk_update instead
                job_from_db.save()

                if newly_completed:
                    job_from_db.refresh_from_db()
                    logger.info(f"{job_from_db.identifier} newly completed")
                    # TODO: port this to here!
                    # handle_job_notifications(job_request, job_from_db)

            # Refresh value of job_request._status so that if we repeatedly call this
            # in a long-running service, we can reliably get a correct list of active
            # job requests.
            # job_request.jobs_status

    logger.info(
        "Created, updated or deleted Jobs",
        created_job_ids=created_job_ids,
        created_job_identifiers=created_job_identifiers,
        updated_job_ids=updated_job_ids,
        updated_job_identifiers=updated_job_identifiers,
        deleted_job_identifiers=deleted_identifiers,
    )
    if json_response["unrecognised_rap_ids"]:
        logger.warning(
            "Unrecognised RAP ids", rap_ids=json_response["unrecognised_rap_ids"]
        )
