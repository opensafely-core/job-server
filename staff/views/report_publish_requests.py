import functools

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, View

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.emails import send_report_published_email
from jobserver.models import ReportPublishRequest


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReportPublishRequestApprove(View):
    context_object_name = "publish_request"
    model = ReportPublishRequest

    def post(self, request, *args, **kwargs):
        publish_request = get_object_or_404(ReportPublishRequest, pk=self.kwargs["pk"])

        publish_request.approve(user=request.user)
        send_report_published_email(publish_request)

        return redirect(publish_request.get_staff_url())


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReportPublishRequestDetail(DetailView):
    context_object_name = "publish_request"
    model = ReportPublishRequest
    template_name = "staff/report_publish_request_detail.html"


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReportPublishRequestList(ListView):
    model = ReportPublishRequest
    template_name = "staff/report_publish_request_list.html"

    def get_context_data(self, **kwargs):
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

        return super().get_context_data(**kwargs) | {
            "states": states,
        }

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related(
                "decision_by",
                "created_by",
            )
            .order_by("-created_at")
        )

        if q := self.request.GET.get("q"):
            fields = [
                "decision_by__fullname",
                "decision_by__username",
                "created_by__fullname",
                "created_by__username",
                "report__title",
            ]

            # build up Q objects OR'd together.  We need to build them with
            # functools.reduce so we can optionally add the PK filter to the
            # list
            qwargs = functools.reduce(
                Q.__or__, (Q(**{f"{f}__icontains": q}) for f in fields)
            )

            qs = qs.filter(qwargs)

        if state := self.request.GET.get("state"):
            if state == "pending":
                qs = qs.filter(decision=None)
            else:
                qs = qs.filter(decision=state)

        return qs.distinct()


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReportPublishRequestReject(View):
    context_object_name = "publish_request"
    model = ReportPublishRequest

    def post(self, request, *args, **kwargs):
        publish_request = get_object_or_404(ReportPublishRequest, pk=self.kwargs["pk"])

        publish_request.reject(user=request.user)
        send_report_published_email(publish_request)

        return redirect(publish_request.get_staff_url())
