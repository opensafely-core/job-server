import structlog
from django.db import connection, models
from django.db.models import Max, Q
from django.db.models.functions import Greatest
from django.urls import reverse
from django.utils import timezone
from furl import furl


logger = structlog.get_logger(__name__)


class WorkspaceQuerySet(models.QuerySet):
    def with_most_recent_activity_at(self):
        return (
            self.prefetch_related("job_requests")
            .annotate(
                last_jobrequest_created_at=Max("job_requests__created_at"),
                max_updated_at=Max("updated_at"),
            )
            .annotate(
                most_recent_activity_at=Greatest(
                    "last_jobrequest_created_at", "max_updated_at"
                )
            )
        )


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
    )

    name = models.TextField(unique=True)
    branch = models.TextField()
    is_archived = models.BooleanField(default=False)
    should_notify = models.BooleanField(default=False)
    purpose = models.TextField(default="")

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

    objects = WorkspaceQuerySet.as_manager()

    class Meta:
        constraints = [
            # mirror Django's validate_slug validator into the database
            models.CheckConstraint(
                check=Q(name__regex=r"^[-a-zA-Z0-9_]+\Z"),
                name="name_is_valid",
            ),
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
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_analyses_url(self):
        return reverse(
            "workspace-analysis-request-list",
            kwargs={
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_archive_toggle_url(self):
        return reverse(
            "workspace-archive-toggle",
            kwargs={
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
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_files_url(self):
        return reverse(
            "workspace-files-list",
            kwargs={
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_jobs_url(self):
        return reverse(
            "job-request-create",
            kwargs={
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_latest_outputs_download_url(self):
        return reverse(
            "workspace-latest-outputs-download",
            kwargs={
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_latest_outputs_url(self):
        return reverse(
            "workspace-latest-outputs-detail",
            kwargs={
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_logs_url(self):
        return reverse(
            "workspace-logs",
            kwargs={
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_notifications_toggle_url(self):
        return reverse(
            "workspace-notifications-toggle",
            kwargs={
                "project_slug": self.project.slug,
                "workspace_slug": self.name,
            },
        )

    def get_outputs_url(self):
        return reverse(
            "workspace-output-list",
            kwargs={
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

        We're doing this in raw SQL so we can use a CTE to get the latest
        actions, and then join that with the Jobs table to get the status of
        those actions.
        """
        sql = """
        WITH latest_actions AS (
          SELECT
            job.action AS name,
            job.status AS status,
            row_number() OVER (PARTITION BY job.action ORDER BY job.created_at DESC) AS row_num
          FROM
            jobserver_job job
          INNER JOIN jobserver_jobrequest job_request ON (job.job_request_id = job_request.id)
          INNER JOIN jobserver_workspace workspace ON (job_request.workspace_id = workspace.id)
          WHERE workspace.name = %s
        )
        SELECT name, status
        FROM latest_actions
        WHERE row_num = 1
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [self.name])
            return dict(cursor.fetchall())

    @property
    def is_interactive(self):
        return self.name.endswith("-interactive")
