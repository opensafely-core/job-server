import base64
import secrets

import structlog
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Max, Min, Q, prefetch_related_objects
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from furl import furl

from ..permissions.t1oo import project_is_permitted_to_use_t1oo_data
from ..runtime import Runtime


logger = structlog.get_logger(__name__)


def new_id():
    """
    Return a random 16 character lowercase alphanumeric string

    This is used for the cross-system `identifier` fields in both JobRequest
    and Job.  This function is mirrored in job-runner, which sets
    Job.identifier, while this project handles setting JobRequest.identifier.

    We used to use UUID4's but they are unnecessarily long for our purposes
    (particularly the hex representation) and shorter IDs make debugging
    and inspecting the job-runner a bit more ergonomic.
    """
    return base64.b32encode(secrets.token_bytes(10)).decode("ascii").lower()


class JobRequestQuerySet(models.QuerySet):
    def with_started_at(self):
        return self.prefetch_related("jobs").annotate(
            started_at=Min("jobs__started_at")
        )


class JobRequestManager(models.Manager.from_queryset(JobRequestQuerySet)):
    use_in_migrations = True

    def previous(self, job_request, filter_succeeded=None):
        workspace_backend_job_requests = super().filter(
            workspace=job_request.workspace,
            backend=job_request.backend,
            id__lt=job_request.id,
        )
        if filter_succeeded:
            # "succeeded" is the last in an alphabetical sort of the statuses, so
            # if the minimum of the related Job's statuses is "succeeded" then they
            # all must be. There are no constraints on this field, however, so
            # checking the maximum as well ensure this is robust to new statuses
            # which would sort later than "succeeded"
            workspace_backend_job_requests = workspace_backend_job_requests.annotate(
                min_status=Min("jobs__status"), max_status=Max("jobs__status")
            ).filter(min_status="succeeded", max_status="succeeded")
        return workspace_backend_job_requests.order_by("created_at").last()


class JobRequestStatus(models.TextChoices):
    """
    Overall status of a JobRequest, used to populate JobRequest.status

    This is a deliberate superset of Job.status, which corresponds to the coarse job State in the
    RAP controller. When setting overall job request status from the status of in-progress/completed jobs,
    it's useful to be able to use the aggregated jobs' status to identify the appropriate JobRequestStatus
    to assign.
    https://github.com/opensafely-core/job-runner/blob/97be1b84e4cd44551965af3d9929b52f88099ff2/controller/models.py#L27
    """

    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
    NOTHING_TO_DO = "nothing_to_do"
    UNKNOWN = "unknown"

    @classmethod
    def is_completed(cls, value):
        completed_states = [cls.FAILED, cls.SUCCEEDED, cls.NOTHING_TO_DO]
        return value and cls(value) in completed_states


class JobRequest(models.Model):
    """
    A request to run a Job

    This represents the request, from a Human, to run a given Job in a
    Workspace.  A job-runner will create any required Jobs for the requested
    one(s) to run.  All Jobs are then grouped by this object.
    """

    backend = models.ForeignKey(
        "Backend", on_delete=models.PROTECT, related_name="job_requests"
    )
    workspace = models.ForeignKey(
        "Workspace", on_delete=models.CASCADE, related_name="job_requests"
    )

    force_run_dependencies = models.BooleanField(default=False)
    cancelled_actions = models.JSONField(default=list)
    requested_actions = ArrayField(models.TextField())
    sha = models.TextField()
    identifier = models.TextField(default=new_id, unique=True)
    will_notify = models.BooleanField(default=False)
    project_definition = models.TextField(default="")
    codelists_ok = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="job_requests",
    )

    # overall status of the JobRequest. If the RAP API did not create any jobs (or failed),
    # this may be populated immediately. Otherwise, it is updated based on the progess and
    # completion of associated jobs.
    status = models.TextField(
        default=JobRequestStatus.UNKNOWN, choices=JobRequestStatus
    )
    status_message = models.TextField(null=True, blank=True)

    objects = JobRequestManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        created_at__isnull=True,
                        created_by__isnull=True,
                    )
                    | (
                        Q(
                            created_at__isnull=False,
                            created_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_created_at_and_created_by_set",
            ),
        ]

    def __str__(self):
        return str(self.pk)

    @cached_property
    def completed_at(self):
        last_job = self.jobs.order_by("completed_at").last()

        if not last_job:
            return

        if not self.is_completed:
            return

        return last_job.completed_at

    def get_absolute_url(self):
        return reverse(
            "job-request-detail",
            kwargs={
                "project_slug": self.workspace.project.slug,
                "workspace_slug": self.workspace.name,
                "pk": self.pk,
            },
        )

    def get_cancel_url(self):
        return reverse(
            "job-request-cancel",
            kwargs={
                "project_slug": self.workspace.project.slug,
                "workspace_slug": self.workspace.name,
                "pk": self.pk,
            },
        )

    def get_file_url(self, path):
        f = furl(self.workspace.repo.url)

        if not self.sha:
            logger.info("No SHA found", job_request_pk=self.pk)
            return f.url

        parts = path.split("/")
        f.path.segments += ["blob", self.sha, *parts]
        return f.url

    def get_repo_url(self):
        f = furl(self.workspace.repo.url)

        if not self.sha:
            logger.info("No SHA found", job_request_pk=self.pk)
            return f.url

        f.path.segments += ["tree", self.sha]
        return f.url

    def get_staff_url(self):
        return reverse(
            "staff:job-request-detail",
            kwargs={
                "pk": self.pk,
            },
        )

    def get_staff_cancel_url(self):
        return reverse(
            "staff:job-request-cancel",
            kwargs={
                "pk": self.pk,
            },
        )

    @property
    def is_completed(self):
        # Is this job request in a completed status? We use the self.jobs_status
        # property here, which will first check the overall jobs_status, and
        # if necessary, calculate status from pending/running jobs
        return JobRequestStatus.is_completed(self.jobs_status)

    @property
    def num_completed(self):
        return len([j for j in self.jobs.all() if j.status == "succeeded"])

    def get_active_actions(self):
        # Active actions are pending or running
        return set(
            self.jobs.exclude(status__in=["failed", "succeeded"]).values_list(
                "action", flat=True
            )
        )

    @property
    def has_cancellable_actions(self):
        # Cancellable actions are ones that are running or pending, and have not already
        # been requested for cancellation (i.e. are not already in self.cancelled_actions
        return self.get_active_actions() - set(self.cancelled_actions)

    def request_cancellation(self):
        # Exclude succeeded jobs (failed or succeeded status, consistent with Job.is_completed method)
        self.cancelled_actions = list(self.get_active_actions())
        self.save(update_fields=["cancelled_actions"])

    @property
    def runtime(self):
        """
        Combined runtime for all completed Jobs of this JobRequest

        Runtime of each completed Job is added together, rather than using the
        delta of the first start time and last completed time.
        """
        if self.started_at is None:
            return Runtime(0, 0, 0)

        def runtime_in_seconds(job):
            if job.started_at is None or job.completed_at is None:
                return 0

            return (job.completed_at - job.started_at).total_seconds()

        # Only look at jobs which have completed
        jobs = self.jobs.filter(Q(status="failed") | Q(status="succeeded"))
        total_runtime = sum(runtime_in_seconds(j) for j in jobs)

        hours, remainder = divmod(total_runtime, 3600)
        minutes, seconds = divmod(remainder, 60)

        return Runtime(int(hours), int(minutes), int(seconds))

    @property
    def jobs_status(self) -> str:
        # status has already been set to a completed status, we can just
        # return it
        if JobRequestStatus.is_completed(self.status):
            return self.status

        prefetched_jobs = (
            hasattr(self, "_prefetched_objects_cache")
            and "jobs" in self._prefetched_objects_cache
        )
        if not prefetched_jobs:
            # require Jobs are prefetched to get statuses since we have to
            # query every Job for the logic below to work
            prefetch_related_objects([self], "jobs")

        # always make use of prefetched Jobs, so we don't execute O(N) queries
        # each time.
        statuses = [j.status for j in self.jobs.all()]

        # when they're all the same, just use that
        if len(set(statuses)) == 1:
            if not statuses[0]:
                # If jobs have been created but have no status set, assume they're pending
                status = JobRequestStatus.PENDING
            else:
                status = JobRequestStatus(statuses[0])
            message = (
                "Failed due to job failure"
                if status == JobRequestStatus.FAILED
                else None
            )
            job_request_status = self.update_status(status, message)

        # if any status is running then the JobRequest is running
        elif "running" in statuses:
            job_request_status = self.update_status(JobRequestStatus.RUNNING)

        # we've eliminated all statuses being the same so any pending statuses
        # at this point mean there are other Jobs which are
        # running/failed/succeeded so the request is still running
        elif "pending" in statuses:
            job_request_status = self.update_status(JobRequestStatus.RUNNING)

        # now we know we have no pending or running Jobs left, that leaves us
        # with failed or succeeded and a JobRequest is failed if any of its
        # Jobs have failed.
        elif "failed" in statuses:
            job_request_status = self.update_status(
                JobRequestStatus.FAILED, "Failed due to job failure"
            )

        else:
            job_request_status = self.update_status(JobRequestStatus.UNKNOWN)

        return job_request_status.value

    def update_status(
        self, new_status: JobRequestStatus, message=None
    ) -> JobRequestStatus:
        if self.status != new_status.value:
            self.status = new_status
            self.status_message = message
            self.save()
        return new_status

    @property
    def database_name(self):
        if project_is_permitted_to_use_t1oo_data(self.workspace.project):
            return "include_t1oo"
        else:
            return "default"
