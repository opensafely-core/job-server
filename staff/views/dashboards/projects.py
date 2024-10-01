import itertools

from csp.decorators import csp_exempt
from django.db.models import Count, Min, Prefetch
from django.db.models.functions import Least, Lower
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from jobserver.authorization import StaffAreaAdministrator
from jobserver.authorization.decorators import require_role
from jobserver.models import Org, Project, ReleaseFile


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
@method_decorator(csp_exempt, name="dispatch")
class ProjectsDashboard(TemplateView):
    template_name = "staff/dashboards/projects.html"

    def get_context_data(self, **kwargs):
        projects = (
            Project.objects.select_related("copilot")
            .prefetch_related(
                Prefetch("orgs", queryset=Org.objects.order_by(Lower("name")))
            )
            .annotate(
                org_count=Count("orgs", distinct=True),
                workspace_count=Count("workspaces", distinct=True),
                job_request_count=Count("workspaces__job_requests", distinct=True),
                date_first_run=Min(
                    Least(
                        "workspaces__job_requests__jobs__started_at",
                        "workspaces__job_requests__jobs__created_at",
                    )
                ),
            )
            .order_by(Lower("name"))
            .iterator(chunk_size=300)
        )

        release_files_by_project = itertools.groupby(
            ReleaseFile.objects.select_related("workspace__project")
            .order_by("workspace__project__pk")
            .iterator(),
            key=lambda f: f.workspace.project.pk,
        )
        file_counts_by_project = {
            p: len(list(files)) for p, files in release_files_by_project
        }

        def iter_projects(projects, file_counts_by_project):
            """
            Build a project representation

            Looking up a number of files released for a project as an annotation
            on the main `projects` query makes Postgres very unhappy and it's
            not obvious how to fix that from the query planner.  This function
            combines the ReleaseFile data (which we've grouped by Project PK) and
            the general project representation.

            Note: we could handle all stats this way but at the time of writing
            the current annotations were performant.
            """
            for project in projects:
                files_released_count = file_counts_by_project.get(project.pk, 0)

                yield {
                    "copilot": project.copilot,
                    "date_first_run": project.date_first_run,
                    "files_released_count": files_released_count,
                    "get_staff_url": project.get_staff_url(),
                    "job_request_count": project.job_request_count,
                    "name": project.name,
                    "number": project.number,
                    "org_count": project.org_count,
                    "orgs": project.orgs.all(),
                    "workspace_count": project.workspace_count,
                }

        projects = list(iter_projects(projects, file_counts_by_project))

        return super().get_context_data(**kwargs) | {
            "projects": projects,
        }
