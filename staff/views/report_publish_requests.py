import functools

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, View

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.models import ReportPublishRequest


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReportPublishRequestApprove(View):
    context_object_name = "publish_request"
    model = ReportPublishRequest

    def post(self, request, *args, **kwargs):
        publish_request = get_object_or_404(ReportPublishRequest, pk=self.kwargs["pk"])

        publish_request.approve(user=request.user)

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

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related(
                "approved_by",
                "created_by",
            )
            .order_by("-created_at")
        )

        if q := self.request.GET.get("q"):
            fields = [
                "approved_by__fullname",
                "approved_by__username",
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

        if self.request.GET.get("is_approved") == "yes":
            qs = qs.exclude(approved_at=None)
        if self.request.GET.get("is_approved") == "no":
            qs = qs.filter(approved_at=None)

        return qs.distinct()
