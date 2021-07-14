import base64
import itertools
import secrets
from datetime import timedelta

import structlog
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.core import signing
from django.core.validators import validate_slug
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from environs import Env
from furl import furl

from ..authorization.fields import ExtractRoles, RolesField
from ..authorization.utils import strings_to_roles
from ..runtime import Runtime
from ..utils import dotted_path


env = Env()
logger = structlog.get_logger(__name__)


def new_id():
    """
    Return a random 16 character lowercase alphanumeric string
    We used to use UUID4's but they are unnecessarily long for our purposes
    (particularly the hex representation) and shorter IDs make debugging
    and inspecting the job-runner a bit more ergonomic.
    """
    return base64.b32encode(secrets.token_bytes(10)).decode("ascii").lower()


class Job(models.Model):
    """
    The execution of an action on a Backend

    We expect this model to only be written to, via the API, by a job-runner.
    """

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

    @property
    def is_completed(self):
        return self.status in ["failed", "succeeded"]

    @property
    def is_missing_updates(self):
        """
        Is this Job missing expected updates from job-runner?

        When a Job has yet to finish but we haven't had an update from
        job-runner in >30 minutes we want to show users a warning.
        """
        if self.is_completed:
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
        if not self.is_completed:
            return

        if self.started_at is None or self.completed_at is None:
            return

        delta = self.completed_at - self.started_at
        total_seconds = delta.total_seconds()

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return Runtime(int(hours), int(minutes), int(seconds), int(total_seconds))


class JobRequest(models.Model):
    """
    A request to run a Job

    This represents the request, from a Human, to run a given Job in a
    Workspace.  A job-runner will create any required Jobs for the requested
    one(s) to run.  All Jobs are then grouped by this object.
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
    def is_completed(self):
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
        Combined runtime for all completed Jobs of this JobRequest

        Runtime of each completed Job is added together, rather than using the
        delta of the first start time and last completed time.
        """
        if self.started_at is None:
            return

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
    def started_at(self):
        first_job = self.jobs.exclude(started_at=None).order_by("started_at").first()

        if not first_job:
            return

        return first_job.started_at

    @property
    def status(self):
        prefetched_jobs = (
            hasattr(self, "_prefetched_objects_cache")
            and "jobs" in self._prefetched_objects_cache
        )
        if not prefetched_jobs:
            # require Jobs are prefetched to get statuses since we have to
            # query every Job for the logic below to work
            raise Exception("JobRequest queries must prefetch jobs.")

        # always make use of prefetched Jobs, so we don't execute O(N) queries
        # each time.
        statuses = [j.status for j in self.jobs.all()]

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
    """An Organisation using the platform"""

    name = models.TextField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(default="", blank=True)
    logo = models.TextField(default="", blank=True)

    # track which GitHub Organisations this Org has access to
    github_orgs = models.JSONField(default=list)

    created_at = models.DateTimeField(default=timezone.now)

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
    """Membership of an Organistion for a User"""

    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="created_org_memberships",
        null=True,
    )
    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="org_memberships",
    )

    roles = RolesField()

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ["org", "user"]

    def __str__(self):
        return f"{self.user.username} | {self.org.name}"


class Project(models.Model):
    """
    A public-facing grouping of work on a topic.

    This includes the Workspaces where work is done, the Repos for the code
    driving that work, the IG approvals allowing the work to happen, and any
    Papers which are produced as a result of the work.
    """

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
    description = models.TextField(default="")
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

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.org.name} | {self.name}"

    def get_absolute_url(self):
        return reverse(
            "project-detail",
            kwargs={"org_slug": self.org.slug, "project_slug": self.slug},
        )

    def get_invitation_url(self):
        return reverse(
            "project-invitation-create",
            kwargs={"org_slug": self.org.slug, "project_slug": self.slug},
        )

    def get_releases_url(self):
        return reverse(
            "project-release-list",
            kwargs={"org_slug": self.org.slug, "project_slug": self.slug},
        )

    def get_settings_url(self):
        return reverse(
            "project-settings",
            kwargs={"org_slug": self.org.slug, "project_slug": self.slug},
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)


class ProjectInvitation(models.Model):
    """
    Models an Invitation to join a Project

    If accepted an Invite is linked to a ProjectMembership.
    """

    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="created_project_invitations",
        null=True,
    )
    membership = models.ForeignKey(
        "ProjectMembership",
        on_delete=models.CASCADE,
        related_name="invitations",
        null=True,
    )
    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="project_invitations",
    )

    roles = RolesField()

    created_at = models.DateTimeField(default=timezone.now)
    accepted_at = models.DateTimeField(null=True)

    class Meta:
        unique_together = ["project", "user"]

    def __str__(self):
        return f"{self.user.username} | {self.project.name}"

    @transaction.atomic
    def create_membership(self):
        self.accepted_at = timezone.now()

        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.user,
            roles=self.roles,
        )
        self.membership = membership

        self.save()

    def get_cancel_url(self):
        return reverse(
            "project-cancel-invite",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
            },
        )

    @classmethod
    def get_from_signed_pk(cls, value):
        """Look up a ProjectInvitation from a signed PK"""
        unsigned_pk = ProjectInvitation.signer().unsign(value)

        return ProjectInvitation.objects.get(pk=unsigned_pk)

    def get_invitation_url(self):
        return reverse(
            "project-accept-invite",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "signed_pk": self.signed_pk,
            },
        )

    @property
    def signed_pk(self):
        return ProjectInvitation.signer().sign(self.pk)

    @staticmethod
    def signer():
        """Provide a salted signer instance for Project Invitations"""
        return signing.Signer(salt="project-invitation")


class ProjectMembership(models.Model):
    """
    Membership of a Project for a User

    Membership grants a User abilities in the context of the Project via the
    assigned Roles.
    """

    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )

    roles = RolesField()

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ["project", "user"]

    def __str__(self):
        return f"{self.user.username} | {self.project.name}"

    def get_edit_url(self):
        return reverse(
            "project-membership-edit",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "pk": self.pk,
            },
        )

    def get_remove_url(self):
        return reverse(
            "project-membership-remove",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "pk": self.pk,
            },
        )


class UserQuerySet(models.QuerySet):
    def filter_by_role(self, role):
        """
        Filter the Users by a given Role (class or string)

        Roles are converted to a dotted path and quoted to make sure we filter
        for a dotted path with surrounding quotes.
        """
        if isinstance(role, str):
            role = strings_to_roles([role])[0]

        path = dotted_path(role)

        return self.alias(extracted=ExtractRoles("roles")).filter(
            extracted__contains=f'"{path}"'
        )


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    """
    Custom Manager built from the custom QuerySet above

    This exists so we have a concrete Manager which can be serialised in
    Migrations.
    """

    pass


class User(AbstractUser):
    """
    A custom User model used throughout the codebase

    Using a custom Model allows us to add extra fields trivially, eg Roles.
    """

    backends = models.ManyToManyField(
        "Backend",
        related_name="backends",
        through="BackendMembership",
        through_fields=["user", "backend"],
    )
    orgs = models.ManyToManyField(
        "Org",
        related_name="members",
        through="OrgMembership",
        through_fields=["user", "org"],
    )
    projects = models.ManyToManyField(
        "Project",
        related_name="members",
        through="ProjectMembership",
    )

    notifications_email = models.TextField(default="")

    # has the User been approved by an admin?
    is_approved = models.BooleanField(default=False)

    roles = RolesField()

    objects = UserManager()

    def get_absolute_url(self):
        return reverse("user-detail", kwargs={"username": self.username})

    def get_all_permissions(self):
        """
        Get all Permissions for the current User
        """

        def flatten_perms(roles):
            permissions = itertools.chain.from_iterable(r.permissions for r in roles)
            return list(sorted(set(permissions)))

        orgs = [
            {
                "slug": m.org.slug,
                "permissions": flatten_perms(m.roles),
            }
            for m in self.org_memberships.all()
        ]

        projects = [
            {
                "slug": m.project.slug,
                "permissions": flatten_perms(m.roles),
            }
            for m in self.project_memberships.all()
        ]

        return {
            "global": flatten_perms(self.roles),
            "orgs": orgs,
            "projects": projects,
        }

    def get_all_roles(self):
        """
        Get all Roles for the current User

        Return all Roles for the User, grouping the local-Roles by the objects
        they are contextual to.
        """

        def role_names(roles):
            return list(sorted(r.__name__ for r in roles))

        orgs = [
            {"slug": m.org.slug, "roles": role_names(m.roles)}
            for m in self.org_memberships.all()
        ]

        projects = [
            {"slug": m.project.slug, "roles": role_names(m.roles)}
            for m in self.project_memberships.all()
        ]

        return {
            "global": role_names(self.roles),
            "orgs": orgs,
            "projects": projects,
        }

    @property
    def name(self):
        """Unify the available names for a User."""
        return self.get_full_name() or self.username


class Workspace(models.Model):
    """Models a working directory on a Backend server."""

    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="workspaces",
    )
    project = models.ForeignKey(
        "Project",
        on_delete=models.PROTECT,
        related_name="workspaces",
    )

    name = models.TextField(unique=True, validators=[validate_slug])
    repo = models.TextField(db_index=True)
    branch = models.TextField()
    is_archived = models.BooleanField(default=False)
    should_notify = models.BooleanField(default=False)

    db = models.TextField(choices=[("full", "Full database")], default="full")

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.repo})"

    def get_absolute_url(self):
        return reverse(
            "workspace-detail",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_archive_toggle_url(self):
        return reverse(
            "workspace-archive-toggle",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_current_outputs_url(self):
        return reverse(
            "workspace-current-outputs-detail",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_logs_url(self):
        return reverse(
            "workspace-logs",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_notifications_toggle_url(self):
        return reverse(
            "workspace-notifications-toggle",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_publish_url(self):
        return reverse(
            "workspace-publish",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_releases_url(self):
        return reverse(
            "workspace-release-list",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_releases_api_url(self):
        return reverse(
            "api:release-workspace",
            kwargs={"workspace_name": self.name},
        )

    def get_statuses_url(self):
        return reverse("api:workspace-statuses", kwargs={"name": self.name})

    def get_action_status_lut(self, backend=None):
        """
        Build a lookup table of action -> status

        We need to get the latest status for each action run inside this
        Workspace.
        """
        jobs = Job.objects.filter(job_request__workspace=self)

        if backend:
            jobs = jobs.filter(job_request__backend__name=backend)

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

    @property
    def repo_owner(self):
        """Convert repo URL -> repo name"""
        f = furl(self.repo)

        if not f.path:
            raise Exception("Repo URL not in expected format, appears to have no path")
        return f.path.segments[0]
