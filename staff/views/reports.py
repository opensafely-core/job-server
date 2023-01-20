import functools

from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.models import Org, Project, Report, User


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReportDetail(DetailView):
    model = Report
    template_name = "staff/report_detail.html"


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReportList(ListView):
    model = Report
    template_name = "staff/report_list.html"

    def get_context_data(self, **kwargs):
        orgs = (
            Org.objects.filter(projects__workspaces__files__reports__isnull=False)
            .distinct()
            .order_by(Lower("name"))
        )
        projects = (
            Project.objects.filter(workspaces__files__reports__isnull=False)
            .distinct()
            .order_by("number", Lower("name"))
        )

        # sort in Python because `User.name` is a property to pick either
        # get_full_name() or username depending on which one has been populated
        users = sorted(
            User.objects.filter(reports_created__isnull=False).distinct(),
            key=lambda u: u.name.lower(),
        )
        return super().get_context_data(**kwargs) | {
            "orgs": orgs,
            "projects": projects,
            "users": users,
        }

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related(
                "created_by",
                "release_file",
                "release_file__workspace",
                "release_file__workspace__project",
                "release_file__workspace__project__org",
            )
            .order_by("-created_at")
        )

        if q := self.request.GET.get("q"):
            fields = [
                "created_by__fullname",
                "created_by__username",
                "title",
            ]

            # build up Q objects OR'd together.  We need to build them with
            # functools.reduce so we can optionally add the PK filter to the
            # list
            qwargs = functools.reduce(
                Q.__or__, (Q(**{f"{f}__icontains": q}) for f in fields)
            )

            qs = qs.filter(qwargs)

        if org := self.request.GET.get("org"):
            qs = qs.filter(release_file__workspace__project__org__slug=org)

        if project := self.request.GET.get("project"):
            qs = qs.filter(release_file__workspace__project__slug=project)

        if user := self.request.GET.get("user"):
            qs = qs.filter(created_by__username=user)

        return qs.distinct()
