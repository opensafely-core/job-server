import base64
import binascii
import json
import os
import secrets
from datetime import timedelta

import structlog
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import validate_slug
from django.db import models
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from environs import Env
from furl import furl

from .backends import get_configured_backends
from .fields import RolesField
from .runtime import Runtime


env = Env()
logger = structlog.get_logger(__name__)


def generate_token():
    """Generate a random token string."""
    return binascii.hexlify(os.urandom(20)).decode()


def new_id():
    """
    Return a random 16 character lowercase alphanumeric string
    We used to use UUID4's but they are unnecessarily long for our purposes
    (particularly the hex representation) and shorter IDs make debugging
    and inspecting the job-runner a bit more ergonomic.
    """
    return base64.b32encode(secrets.token_bytes(10)).decode("ascii").lower()


class BackendManager(models.Manager):
    def get_queryset(self):
        """
        Override default QuerySet to limit backends to those configured

        We want to limit the available backends from the database to those
        configured in the environment without changing the backed in model
        validation. Each Backend is created via a migration.  This function
        limits which backends can be looked up via the ORM to the set listed in
        the env.
        """
        # lookup configured backends on demand to make testing easier
        configured_backends = get_configured_backends()

        qs = super().get_queryset()

        if not configured_backends:
            # if no backends are configured, make all available
            return qs

        return qs.filter(name__in=configured_backends)


class Backend(models.Model):
    name = models.TextField(unique=True)
    display_name = models.TextField()

    parent_directory = models.TextField(default="")

    auth_token = models.TextField(default=generate_token)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BackendManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("backend-detail", kwargs={"pk": self.pk})

    def get_rotate_url(self):
        return reverse("backend-rotate-token", kwargs={"pk": self.pk})

    def rotate_token(self):
        self.auth_token = generate_token()
        self.save()


class Job(models.Model):
    job_request = models.ForeignKey(
        "JobRequest",
        on_delete=models.PROTECT,
        related_name="jobs",
    )

    # The unique identifier created by job-runner to reference this Job.  We
    # trust whatever job-runner sets this to.
    identifier = models.TextField(unique=True)

    action = models.TextField()

    # The current state of the Job, as defined by job-runner.
    status = models.TextField()
    status_code = models.TextField(default="", blank=True)
    status_message = models.TextField(default="", blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.action} ({self.pk})"

    def get_absolute_url(self):
        return reverse("job-detail", kwargs={"identifier": self.identifier})

    def get_cancel_url(self):
        return reverse("job-cancel", kwargs={"identifier": self.identifier})

    def get_zombify_url(self):
        return reverse("job-zombify", kwargs={"identifier": self.identifier})

    @property
    def is_finished(self):
        return self.status in ["failed", "succeeded"]

    @property
    def is_missing_updates(self):
        """
        Is this Job missing expected updates from job-runner?

        When a Job has yet to finish but we haven't had an update from
        job-runner in >30 minutes we want to show users a warning.
        """
        if self.is_finished:
            # Job has completed, ignore lack of updates
            return False

        if not self.updated_at:
            # we can't check freshness without updated_at
            return False

        now = timezone.now()
        threshold = timedelta(minutes=30)
        delta = now - self.updated_at

        return delta > threshold

    @property
    def runtime(self):
        if not self.is_finished:
            return

        if self.started_at is None or self.completed_at is None:
            return

        delta = self.completed_at - self.started_at
        total_seconds = delta.total_seconds()

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return Runtime(int(hours), int(minutes), int(seconds), int(total_seconds))


class JobRequestQuerySet(models.QuerySet):
    def acked(self):
        return self.annotate(num_jobs=Count("jobs")).filter(num_jobs__gt=0)

    def unacked(self):
        return self.annotate(num_jobs=Count("jobs")).filter(num_jobs=0)


class JobRequest(models.Model):
    """
    A request to run a Job

    This represents the request, from a Human, to run a given Job in a
    Workspace.  The job-runner will create any required Jobs for the requested
    one to run.  All Jobs, either added by Human or Computer, are then grouped
    by this object.
    """

    backend = models.ForeignKey(
        "Backend", on_delete=models.PROTECT, null=True, related_name="job_requests"
    )
    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="job_requests",
    )
    workspace = models.ForeignKey(
        "Workspace", on_delete=models.CASCADE, related_name="job_requests"
    )

    force_run_dependencies = models.BooleanField(default=False)
    cancelled_actions = models.JSONField(default=list)
    requested_actions = models.JSONField()
    sha = models.TextField()
    identifier = models.TextField(default=new_id, unique=True)
    will_notify = models.BooleanField(default=False)
    project_definition = models.TextField(default="")

    created_at = models.DateTimeField(default=timezone.now)

    objects = JobRequestQuerySet.as_manager()

    def get_absolute_url(self):
        return reverse("job-request-detail", kwargs={"pk": self.pk})

    @property
    def completed_at(self):
        last_job = self.jobs.order_by("completed_at").last()

        if not last_job:
            return

        if self.status not in ["failed", "succeeded"]:
            return

        return last_job.completed_at

    def get_cancel_url(self):
        return reverse("job-request-cancel", kwargs={"pk": self.pk})

    def get_file_url(self, path):
        f = furl(self.workspace.repo)

        if not self.sha:
            logger.info("No SHA found", job_request_pk=self.pk)
            return f.url

        parts = path.split("/")
        f.path.segments += ["blob", self.sha, *parts]
        return f.url

    def get_repo_url(self):
        f = furl(self.workspace.repo)

        if not self.sha:
            logger.info("No SHA found", job_request_pk=self.pk)
            return f.url

        f.path.segments += ["tree", self.sha]
        return f.url

    @property
    def is_finished(self):
        return self.status in ["failed", "succeeded"]

    @property
    def is_invalid(self):
        """
        Is this JobRequest invalid?

        JobRequests are a request for a given configuration to be run on a
        Backend.  That configuration could be unprocessable for a variety of
        reasons when the Backend looks at it.  We currently surface that to
        job-server by job-runner creating a Job with the action `__error__`.
        This property finds Jobs with that action so we can easily see if this
        particular request was valid or not.
        """
        return self.jobs.filter(action="__error__").exists()

    @property
    def num_completed(self):
        return len([j for j in self.jobs.all() if j.status == "succeeded"])

    @property
    def runtime(self):
        """
        Combined runtime for all finished Jobs of this JobRequest

        Runtime of each finished Job is added together, rather than using the
        delta of the first start time and last completed time.
        """
        if self.started_at is None:
            return

        def runtime_in_seconds(job):
            if job.started_at is None or job.completed_at is None:
                return 0

            return (job.completed_at - job.started_at).total_seconds()

        # Only look at jobs which have finished
        jobs = self.jobs.filter(Q(status="failed") | Q(status="succeeded"))
        total_runtime = sum(runtime_in_seconds(j) for j in jobs)

        hours, remainder = divmod(total_runtime, 3600)
        minutes, seconds = divmod(remainder, 60)

        return Runtime(int(hours), int(minutes), int(seconds))

    @property
    def started_at(self):
        first_job = self.jobs.exclude(started_at=None).order_by("started_at").first()

        if not first_job:
            return

        return first_job.started_at

    @property
    def status(self):
        statuses = self.jobs.values_list("status", flat=True)

        # when they're all the same, just use that
        if len(set(statuses)) == 1:
            return statuses[0]

        # if any status is running then the JobRequest is running
        if "running" in statuses:
            return "running"

        # we've eliminated all statuses being the same so any pending statuses
        # at this point mean there are other Jobs which are
        # running/failed/succeeded so the request is still running
        if "pending" in statuses:
            return "running"

        # now we know we have no pending or running Jobs left, that leaves us
        # with failed or succeeded and a JobRequest is failed if any of its
        # Jobs have failed.
        if "failed" in statuses:
            return "failed"

        return "unknown"


class Org(models.Model):
    name = models.TextField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Organisation"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("org-detail", kwargs={"org_slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)


class OrgMembership(models.Model):
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="created_org_memberships",
        null=True,
    )
    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="org_memberships",
    )

    roles = RolesField()

    class Meta:
        unique_together = ["org", "user"]

    def __str__(self):
        return f"{self.user.username} | {self.org.name}"


class Project(models.Model):
    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="projects",
    )
    researcher_registrations = models.ManyToManyField(
        "ResearcherRegistration",
        related_name="projects",
    )

    name = models.TextField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    proposed_start_date = models.DateTimeField(null=True, blank=True)
    proposed_duration = models.TextField(blank=True)

    # Governance approval
    governance_approval_notes = models.TextField(blank=True)
    has_governance_approval = models.BooleanField(default=False)

    # Technical approval
    technical_approval_notes = models.TextField(blank=True)
    has_technical_approval = models.BooleanField(default=False)

    # What is the next step for this Project?
    # We expect this to be driven by a FSM in a later iteration.
    next_step = models.TextField(blank=True)

    # REGISTRATION FIELDS
    # The fields below are based on from our Modified NHSE Form A:
    # https://docs.google.com/document/d/1_Fd124NqrkJeiprra4vSXU5vytQNUnrTfs4ib3L8vo4
    # Section 3 has been removed since it's not used.
    # Section 1
    project_lead = models.TextField()
    email = models.TextField(blank=True)
    telephone = models.TextField(blank=True)
    job_title = models.TextField(blank=True)
    team_name = models.TextField(blank=True)
    region = models.TextField(blank=True)

    # Section 2
    purpose = models.TextField(blank=True)
    requested_data_meets_purpose = models.TextField(blank=True)
    why_data_is_required = models.TextField(blank=True)
    data_access_legal_basis = models.TextField(blank=True)
    satisfying_confidentiality = models.TextField(blank=True)
    ethics_approval = models.TextField(blank=True)
    is_research_on_cmo_priority_list = models.TextField(blank=True)

    # Section 4
    funding_source = models.TextField(blank=True)
    team_details = models.TextField(blank=True)
    previous_experience_with_ehr = models.TextField(blank=True)
    evidence_of_scripting_languages = models.TextField(blank=True)
    evidence_of_sharing_in_public = models.TextField(blank=True)

    # Section 5
    has_signed_declaration = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.org.name} | {self.name}"

    def get_absolute_url(self):
        return reverse(
            "project-detail",
            kwargs={"org_slug": self.org.slug, "project_slug": self.slug},
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)


class ProjectMembership(models.Model):
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="created_project_memberships",
        null=True,
    )
    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )

    roles = RolesField()

    class Meta:
        unique_together = ["project", "user"]

    def __str__(self):
        return f"{self.user.username} | {self.project.name}"


class Release(models.Model):
    # No value in the default Autoid as we are using a content-addressable hash
    # as it. Additionaly it avoids enumeration attacks.
    id = models.TextField(primary_key=True)
    # TODO: link this formally via backend_username once we have a mapping
    # between User and their backend username
    publishing_user = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )
    workspace = models.ForeignKey(
        "Workspace",
        on_delete=models.PROTECT,
        related_name="releases",
    )
    backend = models.ForeignKey(
        "Backend",
        on_delete=models.PROTECT,
        related_name="+",
    )
    published_at = models.DateTimeField(default=timezone.now)
    upload_dir = models.TextField()
    # list of files in the release upload
    files = models.JSONField()
    # store local TPP/EMIS username for audit
    backend_user = models.TextField()

    def file_path(self, filename):
        return settings.RELEASE_STORAGE / self.upload_dir / filename

    @property
    def manifest(self):
        return json.loads(self.file_path("metadata/manifest.json").read_text())


class ResearcherRegistration(models.Model):
    """
    The Registration of a Researcher for a Project

    When registering a new Project 0-N researchers might be named as part of
    the Project.  Instead of requiring they sign up to the service during the
    registration process this model holds their details, and can be attached to
    a User instance if the Project proceeds past registration.
    """

    user = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="researcher_registrations",
    )

    name = models.TextField()
    passed_researcher_training_at = models.DateTimeField()
    is_ons_accredited_researcher = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Stats(models.Model):
    """This holds per-Backend, per-URL API statistics."""

    backend = models.ForeignKey(
        "Backend", on_delete=models.PROTECT, related_name="stats"
    )

    api_last_seen = models.DateTimeField(null=True, blank=True)
    url = models.TextField()

    class Meta:
        unique_together = ["backend", "url"]

    def __str__(self):
        backend = self.backend.name
        last_seen = (
            self.api_last_seen.strftime("%Y-%m-%d %H:%M:%S")
            if self.api_last_seen
            else "never"
        )
        return f"{backend} | {last_seen} | {self.url}"


class User(AbstractUser):
    notifications_email = models.TextField(default="")

    # has the User been approved by an admin?
    is_approved = models.BooleanField(default=False)

    roles = RolesField()

    @property
    def name(self):
        """Unify the available names for a User."""
        return self.get_full_name() or self.username


class Workspace(models.Model):
    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="workspaces",
    )

    name = models.TextField(unique=True, validators=[validate_slug])
    repo = models.TextField(db_index=True)
    branch = models.TextField()
    is_archived = models.BooleanField(default=False)
    should_notify = models.BooleanField(default=False)

    DB_OPTIONS = (
        ("slice", "Cut-down (but real) database"),
        ("full", "Full database"),
    )
    db = models.TextField(choices=DB_OPTIONS)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.repo})"

    def get_absolute_url(self):
        return reverse("workspace-detail", kwargs={"name": self.name})

    def get_archive_toggle_url(self):
        return reverse("workspace-archive-toggle", kwargs={"name": self.name})

    def get_notifications_toggle_url(self):
        return reverse("workspace-notifications-toggle", kwargs={"name": self.name})

    def get_statuses_url(self):
        return reverse("workspace-statuses", kwargs={"name": self.name})

    def get_action_status_lut(self):
        """
        Build a lookup table of action -> status

        We need to get the latest status for each action run inside this
        Workspace.
        """
        jobs = Job.objects.filter(job_request__workspace=self)

        # get all known actions
        actions = set(jobs.values_list("action", flat=True))

        action_status_lut = {}
        for action in actions:
            # get the latest status for an action
            job = jobs.filter(action=action).order_by("-created_at").first()
            action_status_lut[action] = job.status

        return action_status_lut

    @property
    def repo_name(self):
        """Convert repo URL -> repo name"""
        f = furl(self.repo)

        if not f.path:
            raise Exception("Repo URL not in expected format, appears to have no path")
        return f.path.segments[-1]
