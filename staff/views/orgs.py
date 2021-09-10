from django.contrib import messages
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView, UpdateView, View

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.models import Org, OrgMembership, User

from ..forms import OrgAddMemberForm


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class OrgDetail(FormView):
    form_class = OrgAddMemberForm
    template_name = "staff/org_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Org, slug=self.kwargs["slug"])

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        for user in form.cleaned_data["users"]:
            self.object.memberships.create(user_id=user, created_by=self.request.user)

        return redirect(self.object.get_staff_url())

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "members": self.object.members.order_by(Lower("username")),
            "org": self.object,
            "projects": self.object.projects.order_by("name"),
        }

    def get_form_kwargs(self):
        members = self.object.members.values_list("pk", flat=True)
        return super().get_form_kwargs() | {
            "users": User.objects.exclude(pk__in=members).order_by("username"),
        }

    def get_initial(self):
        return super().get_initial() | {
            "users": self.object.members.values_list("pk", flat=True),
        }

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class OrgEdit(UpdateView):
    fields = [
        "name",
    ]
    model = Org
    template_name = "staff/org_edit.html"

    def get_success_url(self):
        return self.object.get_staff_url()


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class OrgList(ListView):
    queryset = Org.objects.order_by("name")
    template_name = "staff/org_list.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "q": self.request.GET.get("q", ""),
        }

    def get_queryset(self):
        qs = super().get_queryset()

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q)

        return qs


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class OrgRemoveMember(View):
    def post(self, request, *args, **kwargs):
        org = get_object_or_404(Org, slug=self.kwargs["slug"])
        username = request.POST.get("username", None)

        try:
            org.memberships.get(user__username=username).delete()
        except OrgMembership.DoesNotExist:
            pass

        messages.success(request, f"Removed {username} from {org.name}")

        return redirect(org.get_staff_url())
