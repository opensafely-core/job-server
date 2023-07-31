from django.db.models import OuterRef, Subquery
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, View

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.emails import send_report_published_email
from jobserver.models import (
    Org,
    Project,
    PublishRequest,
    Report,
    User,
)

from .qwargs_tools import qwargs


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReportDetail(DetailView):
    model = Report
    template_name = "staff/report_detail.html"

    def get_context_data(self, **kwargs):
        publish_requests = self.object.publish_requests.order_by("-created_at")

        return super().get_context_data(**kwargs) | {
            "publish_requests": publish_requests,
        }

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "analysis_request",
                "analysis_request__project",
                "created_by",
                "release_file__workspace__project",
            )
            .prefetch_related("release_file__snapshots__publish_requests")
        )


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

        states = [
            {
                "name": "Approved",
                "slug": "approved",
            },
            {
                "name": "Pending",
                "slug": "pending",
            },
            {
                "name": "Rejected",
                "slug": "rejected",
            },
        ]

        # sort in Python because `User.name` is a property to pick either
        # get_full_name() or username depending on which one has been populated
        users = sorted(
            User.objects.filter(reports_created__isnull=False).distinct(),
            key=lambda u: u.name.lower(),
        )
        return super().get_context_data(**kwargs) | {
            "orgs": orgs,
            "projects": projects,
            "states": states,
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
            )
            .order_by("-created_at")
        )

        if q := self.request.GET.get("q"):
            fields = [
                "created_by__fullname",
                "created_by__username",
                "title",
            ]
            qs = qs.filter(qwargs(fields, q))

        if state := self.request.GET.get("state"):
            # annotate the latest PublishRequest.decision value onto each
            # Report so we can filter by that
            qs = qs.exclude(publish_requests=None).annotate(
                latest_decision=Subquery(
                    PublishRequest.objects.filter(report_id=OuterRef("pk"))
                    .order_by("-created_at")
                    .values("decision")[:1]
                )
            )
            if state == "pending":
                # this isn't a real value for PublishRequest.decision, but
                # represents decision=None, not to be confused with no
                # PublishRequests existing for a Report
                qs = qs.filter(latest_decision=None)
            else:
                qs = qs.filter(latest_decision=state)

        if org := self.request.GET.get("org"):
            qs = qs.filter(release_file__workspace__project__org__slug=org)

        if project := self.request.GET.get("project"):
            qs = qs.filter(release_file__workspace__project__slug=project)

        if user := self.request.GET.get("user"):
            qs = qs.filter(created_by__username=user)

        return qs.distinct()


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReportPublishRequestApprove(View):
    def post(self, request, *args, **kwargs):
        publish_request = get_object_or_404(
            PublishRequest,
            report__pk=self.kwargs["pk"],
            pk=self.kwargs["publish_request_pk"],
        )

        publish_request.approve(user=request.user)
        send_report_published_email(publish_request)

        return redirect(publish_request.report.get_staff_url())


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReportPublishRequestReject(View):
    def post(self, request, *args, **kwargs):
        publish_request = get_object_or_404(
            PublishRequest,
            report__pk=self.kwargs["pk"],
            pk=self.kwargs["publish_request_pk"],
        )

        publish_request.reject(user=request.user)

        return redirect(publish_request.report.get_staff_url())
