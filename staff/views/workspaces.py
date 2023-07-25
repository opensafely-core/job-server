from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, UpdateView

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.models import Workspace

from ..forms import WorkspaceEditForm


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class WorkspaceDetail(DetailView):
    model = Workspace
    slug_field = "name"
    template_name = "staff/workspace_detail.html"

    def get_context_data(self, **kwargs):
        job_requests = self.object.job_requests.select_related("created_by").order_by(
            "-created_at"
        )[:10]
        redirects = self.object.redirects.order_by("old_url")

        return super().get_context_data(**kwargs) | {
            "job_requests": job_requests,
            "redirects": redirects,
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class WorkspaceEdit(UpdateView):
    form_class = WorkspaceEditForm
    model = Workspace
    slug_field = "name"
    template_name = "staff/workspace_edit.html"

    @transaction.atomic()
    def form_valid(self, form):
        # look up the original object from the database because the form will
        # mutation self.object under us
        old = self.get_object()

        form.save()

        # check changed_data here instead of comparing self.object.project to
        # new.project because self.object is mutated when ModelForm._post_clean
        # updates the instance it was passed.  This is because form.instance is
        # set from the passed in self.object.
        if "project" in form.changed_data:
            self.object.redirects.create(
                created_by=self.request.user,
                old_url=old.get_absolute_url(),
            )

        return redirect(self.object.get_staff_url())


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class WorkspaceList(ListView):
    model = Workspace
    ordering = "name"
    template_name = "staff/workspace_list.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "q": self.request.GET.get("q", ""),
        }

    def get_queryset(self):
        qs = super().get_queryset()

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(repo__url__icontains=q))

        return qs
