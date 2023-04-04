import base64
import itertools
import secrets
from datetime import date, timedelta
from urllib.parse import quote

import pydantic
import structlog
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.postgres.fields import ArrayField
from django.core.validators import validate_slug
from django.db import models
from django.db.models import Min, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from environs import Env
from furl import furl
from opentelemetry.trace import propagation
from opentelemetry.trace.propagation import tracecontext
from pipeline import YAMLError, load_pipeline
from sentry_sdk import capture_message
from xkcdpass import xkcd_password

from ..authorization import InteractiveReporter
from ..authorization.fields import RolesField
from ..authorization.utils import strings_to_roles
from ..hash_utils import hash_user_pat
from ..runtime import Runtime


env = Env()
logger = structlog.get_logger(__name__)


def default_github_orgs():
    return list(["opensafely"])


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

    # send from job-runner so we can link direct to a trace
    trace_context = models.JSONField(null=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.action} ({self.pk})"

    def get_absolute_url(self):
        return reverse(
            "job-detail",
            kwargs={
                "org_slug": self.job_request.workspace.project.org.slug,
                "project_slug": self.job_request.workspace.project.slug,
                "workspace_slug": self.job_request.workspace.name,
                "pk": self.job_request.pk,
                "identifier": self.identifier,
            },
        )

    def get_cancel_url(self):
        return reverse(
            "job-cancel",
            kwargs={
                "org_slug": self.job_request.workspace.project.org.slug,
                "project_slug": self.job_request.workspace.project.slug,
                "workspace_slug": self.job_request.workspace.name,
                "pk": self.job_request.pk,
                "identifier": self.identifier,
            },
        )

    def get_redirect_url(self):
        return reverse("job-redirect", kwargs={"identifier": self.identifier})

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
    def run_command(self):
        if not self.job_request.project_definition:
            return

        # load job_request's project_definition into pipeline and get the
        # command for this job
        try:
            pipeline = load_pipeline(self.job_request.project_definition)
        except (pydantic.ValidationError, YAMLError):
            return  # we don't have a valid config

        if action := pipeline.actions.get(self.action):
            command = action.run.run
        else:
            return  # unknown action, likely __error__

        # remove newlines and extra spaces
        return command.replace("\n", "").replace("  ", " ")

    @property
    def runtime(self):
        if not self.is_completed:
            return Runtime(0, 0, 0)

        if self.started_at is None or self.completed_at is None:
            return Runtime(0, 0, 0)

        delta = self.completed_at - self.started_at
        total_seconds = delta.total_seconds()

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return Runtime(int(hours), int(minutes), int(seconds), int(total_seconds))

    @property
    def trace_id(self):
        if not self.trace_context:
            return None  # pragma: no cover

        # this rediculous dance is just because of OTel spec silliness
        ctx = tracecontext.TraceContextTextMapPropagator().extract(
            carrier=self.trace_context
        )
        span_ctx = propagation.get_current_span(ctx).get_span_context()
        return span_ctx.trace_id


class JobRequestManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("jobs")
            .annotate(started_at=Min("jobs__started_at"))
        )


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

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="job_requests",
    )

    objects = JobRequestManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
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

    def get_absolute_url(self):
        return reverse(
            "job-request-detail",
            kwargs={
                "org_slug": self.workspace.project.org.slug,
                "project_slug": self.workspace.project.slug,
                "workspace_slug": self.workspace.name,
                "pk": self.pk,
            },
        )

    @property
    def completed_at(self):
        last_job = self.jobs.order_by("completed_at").last()

        if not last_job:
            return

        if self.status not in ["failed", "succeeded"]:
            return

        return last_job.completed_at

    def get_cancel_url(self):
        return reverse(
            "job-request-cancel",
            kwargs={
                "org_slug": self.workspace.project.org.slug,
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

    created_by = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_orgs",
    )

    name = models.TextField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(default="", blank=True)
    logo = models.TextField(default="", blank=True)
    logo_file = models.FileField(upload_to="org_logos/", null=True)

    # track which GitHub Organisations this Org has access to
    github_orgs = ArrayField(models.TextField(), default=default_github_orgs)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Organisation"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("org-detail", kwargs={"org_slug": self.slug})

    def get_edit_url(self):
        return reverse("staff:org-edit", kwargs={"slug": self.slug})

    def get_staff_url(self):
        return reverse("staff:org-detail", kwargs={"slug": self.slug})

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

    class Statuses(models.TextChoices):
        ONGOING = "ongoing", "Ongoing"
        POSTPONED = "postponed", "Postponed"
        RETIRED = "retired", "Retired"

        # we expect these to go away and be replaced with first class support
        # for linking out to papers and reports but for now we need to track
        # them so they're statuses.
        ONGOING_LINKED = "ongoing-and-linked", "Ongoing - paper/report linked"
        COMPLETED_LINKED = "completed-and-linked", "Completed - paper/report linked"
        COMPLETED_AWAITING = (
            "completed-and-awaiting",
            "Completed - awaiting paper/report",
        )

    copilot = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="copiloted_projects",
    )

    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="projects",
    )

    name = models.TextField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    number = models.IntegerField(null=True)

    copilot_support_ends_at = models.DateTimeField(null=True)

    status = models.TextField(choices=Statuses.choices, default=Statuses.ONGOING)
    status_description = models.TextField(default="", blank=True)

    copilot_notes = models.TextField(default="", blank=True)

    # OSI applications will be done externally.
    # Unfortunately we can't validate this in the db with a CheckConstraint
    # because we can't reference the FK's related_name there.
    application_url = models.TextField(default="")

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_projects",
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="projects_updated",
        null=True,
    )

    class Meta:
        constraints = [
            # only consider uniqueness of number when it's not null
            models.UniqueConstraint(
                fields=["number"],
                name="unique_number_ignore_null",
                condition=Q(number__isnull=False),
            ),
        ]

    def __str__(self):
        return f"{self.org.name} | {self.title}"

    def get_absolute_url(self):
        return reverse(
            "project-detail",
            kwargs={"org_slug": self.org.slug, "project_slug": self.slug},
        )

    def get_approved_url(self):
        f = furl("https://www.opensafely.org/approved-projects")

        if self.number:
            f.fragment = f"project-{self.number}"

        return f.url

    def get_edit_url(self):
        return reverse(
            "project-edit",
            kwargs={"org_slug": self.org.slug, "project_slug": self.slug},
        )

    def get_interactive_url(self):
        return reverse(
            "interactive:analysis-create",
            kwargs={"org_slug": self.org.slug, "project_slug": self.slug},
        )

    def get_staff_edit_url(self):
        return reverse("staff:project-edit", kwargs={"slug": self.slug})

    def get_releases_url(self):
        return reverse(
            "project-release-list",
            kwargs={"org_slug": self.org.slug, "project_slug": self.slug},
        )

    def get_staff_url(self):
        return reverse("staff:project-detail", kwargs={"slug": self.slug})

    def get_staff_feature_flags_url(self):
        return reverse("staff:project-feature-flags", kwargs={"slug": self.slug})

    @property
    def interactive_slug(self):
        return f"{self.slug}-interactive"

    @property
    def interactive_workspace(self):
        return self.workspaces.get(name=self.interactive_slug)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)

    @property
    def title(self):
        if self.number is None:
            return self.name

        return f"{self.number} - {self.name}"


class ProjectMembership(models.Model):
    """
    Membership of a Project for a User

    Membership grants a User abilities in the context of the Project via the
    assigned Roles.
    """

    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="created_project_memberships",
        null=True,
    )
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
        return f"{self.user.username} | {self.project.title}"

    def get_staff_edit_url(self):
        return reverse(
            "staff:project-membership-edit",
            kwargs={
                "slug": self.project.slug,
                "pk": self.pk,
            },
        )

    def get_staff_remove_url(self):
        return reverse(
            "staff:project-membership-remove",
            kwargs={
                "slug": self.project.slug,
                "pk": self.pk,
            },
        )


class Repo(models.Model):
    url = models.TextField(unique=True)
    has_github_outputs = models.BooleanField(default=False)

    internal_signed_off_at = models.DateTimeField(null=True)
    internal_signed_off_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="internally_signed_off_repos",
        null=True,
    )

    researcher_signed_off_at = models.DateTimeField(null=True)
    researcher_signed_off_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        null=True,
        related_name="repos_signed_off_by_researcher",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(
                        internal_signed_off_at__isnull=True,
                        internal_signed_off_by__isnull=True,
                    )
                    | (
                        Q(
                            internal_signed_off_at__isnull=False,
                            internal_signed_off_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_internal_signed_off_at_and_internal_signed_off_by_set",
            ),
            models.CheckConstraint(
                check=(
                    Q(
                        researcher_signed_off_at__isnull=True,
                        researcher_signed_off_by__isnull=True,
                    )
                    | (
                        Q(
                            researcher_signed_off_at__isnull=False,
                            researcher_signed_off_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_researcher_signed_off_at_and_researcher_signed_off_by_set",
            ),
        ]

    def __str__(self):
        return self.url

    def get_handler_url(self):
        return reverse("repo-handler", kwargs={"repo_url": self.quoted_url})

    def get_sign_off_url(self):
        return reverse("repo-sign-off", kwargs={"repo_url": self.quoted_url})

    def get_staff_sign_off_url(self):
        return reverse("staff:repo-sign-off", kwargs={"repo_url": self.quoted_url})

    def get_staff_url(self):
        return reverse("staff:repo-detail", kwargs={"repo_url": self.quoted_url})

    @property
    def name(self):
        """Convert repo URL -> repo name"""
        return self._url().path.segments[-1]

    @property
    def owner(self):
        """Convert repo URL -> repo owner"""
        return self._url().path.segments[0]

    @property
    def quoted_url(self):
        return quote(self.url, safe="")

    def _url(self):
        f = furl(self.url)

        if not f.path:
            raise Exception("Repo URL not in expected format, appears to have no path")

        return f


class UserQuerySet(models.QuerySet):
    def filter_by_role(self, role):
        """
        Filter the Users by a given Role (class or string)

        Roles are converted to a dotted path and quoted to make sure we filter
        for a dotted path with surrounding quotes.
        """
        if isinstance(role, str):
            role = strings_to_roles([role])[0]

        return self.filter(roles__contains=[role])


class UserManager(BaseUserManager.from_queryset(UserQuerySet), BaseUserManager):
    """
    Custom Manager built from the custom QuerySet above

    This exists so we have a concrete Manager which can be serialised in
    Migrations.
    """

    pass


WORDLIST = xkcd_password.generate_wordlist("eff-long")


def human_memorable_token(size=8):
    """Generate a 3 short english words from the eff-long list of words."""
    return xkcd_password.generate_xkcdpassword(WORDLIST, numwords=3)


class User(AbstractBaseUser):
    """
    A custom User model used throughout the codebase

    Using a custom Model allows us to add extra fields trivially, eg Roles.
    """

    backends = models.ManyToManyField(
        "Backend",
        related_name="members",
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
        through_fields=["user", "project"],
    )

    username_validator = UnicodeUsernameValidator()
    username = models.TextField(
        unique=True,
        validators=[username_validator],
        error_messages={"unique": "A user with that username already exists."},
    )
    email = models.EmailField(blank=True, unique=True)

    # fullname instead of full_name because social auth already provides that
    # field name and life is too short to work out which class we should map
    # fullname -> full_name in.
    # TODO: rename name and remove the name property once all users have filled
    # in their names
    fullname = models.TextField(default="")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField("date joined", default=timezone.now)

    notifications_email = models.TextField(default="")

    # has the User been approved by an admin?
    is_approved = models.BooleanField(default=False)

    # PATs are generated for bot users.  They can only be generated via a shell
    # so they can't be accidentally exposed via the UI.
    pat_token = models.TextField(null=True, unique=True)
    pat_expires_at = models.DateTimeField(null=True)

    # single use token login
    login_token = models.TextField(null=True)
    login_token_expires_at = models.DateTimeField(null=True)

    # normally this would be nullable but we are only creating users for
    # Interactive users currently
    created_by = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
    )

    roles = RolesField()

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(
                        pat_expires_at__isnull=True,
                        pat_token__isnull=True,
                    )
                    | Q(
                        pat_expires_at__isnull=False,
                        pat_token__isnull=False,
                    )
                ),
                name="%(app_label)s_%(class)s_both_pat_expires_at_and_pat_token_set",
            ),
            # only consider uniqueness of notifications_email when it's not empty
            models.UniqueConstraint(
                fields=["notifications_email"],
                name="unique_notifications_email_ignore_empty",
                condition=~Q(notifications_email=""),
            ),
        ]

    def __str__(self):
        return self.name

    @cached_property
    def all_roles(self):
        """
        All roles, including those given via memberships, for the User

        Typically we look up whether the user has permission or a role in the
        context of another object (eg a project).  However there are times when
        we want to check all the roles available to a user.  This property
        allows us to use typical python membership checks when doing that, eg:

            if InteractiveReporter not in user.all_roles:
        """
        membership_roles = list(
            itertools.chain.from_iterable(
                [m.roles for m in self.project_memberships.all()]
                + [m.roles for m in self.org_memberships.all()]
            )
        )

        return set(self.roles + membership_roles)

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    @property
    def initials(self):
        if self.name == self.username:
            return self.name[0].upper()

        return "".join(w[0].upper() for w in self.name.split(" "))

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

    def get_full_name(self):
        """Support Django's User contract"""
        return self.fullname

    def get_staff_url(self):
        return reverse("staff:user-detail", kwargs={"username": self.username})

    def has_valid_pat(self, full_token):
        if not full_token:
            return False

        pat_token = hash_user_pat(full_token)
        if not secrets.compare_digest(pat_token, self.pat_token):
            return False

        if self.pat_expires_at.date() < date.today():
            capture_message(f"Expired token for {self.username}")
            return False

        return True

    @property
    def is_interactive_only(self):
        """
        Does this user only have access the Interactive part of the platform

        Because a user can have the InteractiveReporter role globally or via
        any project, along with other roles, we needed an easy way to identify
        when a user has only this role.
        """
        return self.all_roles == {InteractiveReporter}

    @property
    def name(self):
        """Unify the available names for a User."""
        return self.fullname or self.username

    def rotate_token(self):
        # ticket to look at signing request
        expires_at = timezone.now() + timedelta(days=90)

        # store as datetime in case we want to compare with a datetime or
        # increase resolution later.
        expires_at = expires_at.replace(hour=0, minute=0, second=0, microsecond=0)

        # suffix the token with the expiry date so it's clearer to users of it
        # when it will expire
        token = f"{secrets.token_hex(32)}-{expires_at.date().isoformat()}"

        # we're going to check the token against ones passed to the service,
        # but we don't want to expose ourselves to timing attacks.  So we're
        # storing it in the db as a hased string using Django's password
        # hashing tools and then comparing (in User.is_valid_pat()) with
        # secrets.compare_digest to avoid a timing attack there.
        hashed_token = hash_user_pat(token)

        self.pat_expires_at = expires_at
        self.pat_token = hashed_token
        self.save(update_fields=["pat_token", "pat_expires_at"])

        # return the unhashed token so it can be passed to a consuming service
        return token

    class BadLoginToken(Exception):
        pass

    class ExpiredLoginToken(Exception):
        pass

    def _strip_token(self, token):
        return token.strip().replace(" ", "")

    def generate_login_token(self):
        """Generate, set and return single use login token and expiry"""
        token = human_memorable_token()
        self.login_token = make_password(self._strip_token(token))
        self.login_token_expires_at = timezone.now() + timedelta(hours=1)
        self.save(update_fields=["login_token_expires_at", "login_token"])
        return token

    def validate_login_token(self, token):

        if not (self.login_token and self.login_token_expires_at):
            raise self.BadLoginToken(f"No login token set for {self.username}")

        if timezone.now() > self.login_token_expires_at:
            raise self.ExpiredLoginToken(f"Token for {self.username} has expired")

        if not check_password(self._strip_token(token), self.login_token):
            raise self.BadLoginToken(f"Token for {self.username} was invalid")

        # all good - consume this token
        self.login_token = self.login_token_expires_at = None
        self.save(update_fields=["login_token_expires_at", "login_token"])


class Workspace(models.Model):
    """Models a working directory on a Backend server."""

    project = models.ForeignKey(
        "Project",
        on_delete=models.PROTECT,
        related_name="workspaces",
    )
    repo = models.ForeignKey(
        "Repo",
        on_delete=models.PROTECT,
        related_name="workspaces",
        null=True,
    )

    name = models.TextField(unique=True, validators=[validate_slug])
    branch = models.TextField()
    is_archived = models.BooleanField(default=False)
    should_notify = models.BooleanField(default=False)
    purpose = models.TextField(default="")

    db = models.TextField(choices=[("full", "Full database")], default="full")

    # TODO: Remove this once all Projects are ready to move to the new release
    # process
    uses_new_release_flow = models.BooleanField(default=True)

    signed_off_at = models.DateTimeField(null=True)
    signed_off_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        null=True,
        related_name="workspaces_signed_off",
    )

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="workspaces",
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="workspaces_updated",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
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
            models.CheckConstraint(
                check=(
                    Q(
                        signed_off_at__isnull=True,
                        signed_off_by__isnull=True,
                    )
                    | (
                        Q(
                            signed_off_at__isnull=False,
                            signed_off_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_signed_off_at_and_signed_off_by_set",
            ),
            models.CheckConstraint(
                check=Q(updated_at__isnull=False, updated_by__isnull=False),
                name="%(app_label)s_%(class)s_both_updated_at_and_updated_by_set",
            ),
        ]

    def __str__(self):
        return self.name

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

    def get_create_snapshot_api_url(self):
        return reverse("api:snapshot-create", kwargs={"workspace_id": self.name})

    def get_edit_url(self):
        return reverse(
            "workspace-edit",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_files_url(self):
        return reverse(
            "workspace-files-list",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_jobs_url(self):
        return reverse(
            "job-request-create",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_latest_outputs_download_url(self):
        return reverse(
            "workspace-latest-outputs-download",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_latest_outputs_url(self):
        return reverse(
            "workspace-latest-outputs-detail",
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

    def get_outputs_url(self):
        return reverse(
            "workspace-output-list",
            kwargs={
                "org_slug": self.project.org.slug,
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_readme_url(self):
        f = furl(self.repo)
        f.path.segments += [
            "blob",
            self.branch,
            "README.md",
        ]
        return f.url

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

    def get_staff_url(self):
        return reverse("staff:workspace-detail", kwargs={"slug": self.name})

    def get_staff_edit_url(self):
        return reverse("staff:workspace-edit", kwargs={"slug": self.name})

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
            jobs = jobs.filter(job_request__backend__slug=backend)

        # get all known actions
        actions = set(jobs.values_list("action", flat=True))

        action_status_lut = {}
        for action in actions:
            # get the latest status for an action
            job = jobs.filter(action=action).order_by("-created_at").first()
            action_status_lut[action] = job.status
        return action_status_lut

    @property
    def is_interactive(self):
        return self.name.endswith("-interactive")
