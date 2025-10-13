import datetime

import structlog
from django.db.models import Q
from django.utils import timezone

from jobserver import rap_api
from jobserver.models import Job, JobRequest, JobRequestStatus
from jobserver.models.job import COMPLETED_STATES


logger = structlog.get_logger(__name__)


def get_active_job_request_identifiers():
    # For interim RAP API s2 work, this only finds Jobs/JobRequests for the test backend
    active_job_jobrequest_ids = (
        Job.objects.filter(
            status__in=["pending", "running"], job_request__backend__slug="test"
        )
        .values_list("job_request_id")
        .distinct()
    )
    # We also filter JobRequests that we identify by their _status field to only those created within the
    # past year, to avoid returning any very old job requests that may have unknown status due to
    # historical differences in the way the job status field was set.
    one_year_ago = timezone.now() - datetime.timedelta(weeks=52)
    active_job_requests = JobRequest.objects.filter(
        Q(
            _status__in=JobRequest.active_statuses,
            created_at__gte=one_year_ago,
            backend__slug="test",
        )
        | Q(id__in=active_job_jobrequest_ids)
    )
    # recheck .jobs_status as ._status from the database can be stale
    return [
        jr.identifier
        for jr in active_job_requests
        if jr.jobs_status in JobRequest.active_statuses
    ]


def rap_status_update(rap_ids):
    json_response = rap_api.status(
        rap_ids,
    )
    job_request_by_identifier = (
        JobRequest.objects.filter(identifier__in=rap_ids)
        .prefetch_related("jobs")
        .in_bulk(field_name="identifier")
    )
    # Retrieve all pre-update job statuses for existing jobs before updates so
    # we can idenitfy those that have newly completed
    preupdate_job_statuses = {
        job.identifier: job.status
        for jr in job_request_by_identifier.values()
        for job in jr.jobs.all()
    }

    created_job_ids = []
    created_job_identifiers = []
    updated_job_ids = []
    updated_job_identifiers = []
    unrecognised_job_identifiers = []
    failed_job_request_identifiers = []

    # Turn job response data into a dict of jobs by rap_id
    # Also remove rap_id from the job data - it's going to be set by
    # creating/updating Job instances via the JobRequest instances
    # related Jobs manager (ie job_request.jobs)
    # Also remove some other values which we don't currently store in Job
    jobs_from_api_by_rap_id = {}
    for job in json_response["jobs"]:
        job_rap_id = job.pop("rap_id")
        for superfluous_job_key in ["backend", "requires_db"]:
            job.pop(superfluous_job_key, None)
        jobs_from_api_by_rap_id.setdefault(job_rap_id, []).append(job)

    unrecognised_rap_ids = set(json_response.get("unrecognised_rap_ids", []))

    for rap_id in rap_ids:
        job_request = job_request_by_identifier.get(rap_id)

        if rap_id in unrecognised_rap_ids:
            # If this job request got an unknown error when initially creating jobs, it means that the RAP
            # API was called, but we couldn't tell whether jobs were created on the controller or not.
            # We now know that they were not successfully created, so we can mark the job request as failed
            # We don't do anything with job requests that have any other status, because we can't be sure of
            # why there are no jobs on the controller, so we just log those as errors later.
            if job_request.jobs_status == JobRequestStatus.UNKNOWN_ERROR_CREATING_JOBS:
                job_request.update_status(
                    JobRequestStatus.FAILED, "Unknown error creating jobs"
                )
                failed_job_request_identifiers.append(rap_id)
            continue

        # This could happen if the management command is given a rap_id which
        # does not exist on job-server but does exist on the controller.
        if job_request is None:
            logger.warning("Job-server does not recognise RAP id", rap_id=rap_id)
            continue

        # bind the job request ID to further logs so looking them up
        # in the UI is easier
        with structlog.contextvars.bound_contextvars(job_request=job_request.id):
            jobs_from_api = jobs_from_api_by_rap_id.get(rap_id, [])
            # get the current Jobs for the JobRequest, keyed on their identifier
            database_identifiers = {j.identifier for j in job_request.jobs.all()}

            payload_identifiers = {j["identifier"] for j in jobs_from_api}

            # check for local jobs not in the payload. This should never happen - jobs
            # are only created via an update from the RAP controller. Collect thse so we
            # can log and emit a sentry event.
            unrecognised_identifiers = set(database_identifiers) - payload_identifiers
            if unrecognised_identifiers:
                unrecognised_job_identifiers.extend(unrecognised_identifiers)

            for job_from_api in jobs_from_api:
                logger.debug(
                    "RAP Job Status",
                    rap_id=rap_id,
                    job_identifier=job_from_api["identifier"],
                    status=job_from_api["status"],
                )

                job_from_db: Job
                # Note: we use update_or_create here as it uses select_for_update behind the
                # scenes and locks the row until it's done. We may be able to remove this once
                # the RAP API V2 work is complete and the controller no longer also calls
                # the API jobs endpoint to update.
                job_from_db, created = job_request.jobs.update_or_create(
                    identifier=job_from_api["identifier"],
                    defaults={**job_from_api},
                )

                if created:
                    created_job_ids.append(job_from_db.id)
                    created_job_identifiers.append(job_from_db.identifier)
                    # For newly created jobs we can't tell if they've just
                    # transitioned to completed so we assume they have to avoid
                    # missing notifications
                    newly_completed = job_from_db.is_completed
                else:
                    updated_job_ids.append(job_from_db.id)
                    updated_job_identifiers.append(job_from_db.identifier)

                    newly_completed = (
                        preupdate_job_statuses.get(job_from_db.identifier)
                        not in COMPLETED_STATES
                        and job_from_api["status"] in COMPLETED_STATES
                    )

                if newly_completed:
                    logger.debug(
                        "Newly completed job", job_identifier=job_from_db.identifier
                    )
                    # TODO: port this to here!
                    # handle_job_notifications(job_request, job_from_db)

            # TODO: Use bulk_create with update_conflicts=True to bulk create or update

    if created_job_ids or updated_job_ids:
        logger.info(
            "Created or updated Jobs",
            created_job_ids=created_job_ids,
            created_job_identifiers=created_job_identifiers,
            updated_job_ids=updated_job_ids,
            updated_job_identifiers=updated_job_identifiers,
        )
    if unrecognised_job_identifiers:
        # TODO: Emit sentry event
        logger.error(
            "Locally existing jobs missing from RAP API response",
            unrecognised_job_identifiers=unrecognised_job_identifiers,
        )
    if json_response["unrecognised_rap_ids"]:
        logger.warning(
            "Unrecognised RAP ids", rap_ids=json_response["unrecognised_rap_ids"]
        )
    if failed_job_request_identifiers:
        logger.info(
            "Job requests with no RAP jobs updated to failed",
            rap_ids=failed_job_request_identifiers,
        )
