from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from jobserver.models import Org, Project, Workspace


@method_decorator(login_required, name="dispatch")
class OrgList(ListView):
    model = Org
    ordering = "name"
    paginate_by = 20
    template_name = "yours/org_list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(pk__in=self.request.user.orgs.values_list("pk"))
        )


@method_decorator(login_required, name="dispatch")
class ProjectList(ListView):
    model = Project
    ordering = "name"
    paginate_by = 20
    template_name = "yours/project_list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(pk__in=self.request.user.projects.values_list("pk"))
        )


@method_decorator(login_required, name="dispatch")
class WorkspaceList(ListView):
    model = Workspace
    ordering = "name"
    paginate_by = 20
    template_name = "yours/workspace_list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(project__in=self.request.user.projects.all())
            .select_related("project")
        )
