from django.contrib import messages
from django.db import transaction
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, FormView, ListView, UpdateView, View
from django_htmx.http import HttpResponseClientRedirect

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_permission, require_role
from jobserver.models import Org, OrgMembership, Project, User

from ..forms import OrgAddGitHubOrgForm, OrgAddMemberForm


@require_role(CoreDeveloper)
def org_add_github_org(request, slug):
    org = get_object_or_404(Org, slug=slug)

    if request.POST:
        form = OrgAddGitHubOrgForm(data=request.POST)
    else:
        form = OrgAddGitHubOrgForm()

    if request.GET or not form.is_valid():
        return TemplateResponse(
            context={"form": form, "org": org},
            request=request,
            template="staff/org_add_github_orgs.htmx.html",
        )

    name = form.cleaned_data["name"]
    org.github_orgs.append(name)
    org.save()

    return redirect(org.get_staff_url())


@method_decorator(require_permission("org_create"), name="dispatch")
class OrgCreate(CreateView):
    fields = ["name"]
    model = Org

    def form_valid(self, form):
        org = form.save(commit=False)
        org.created_by = self.request.user
        org.save()

        org_detail = org.get_staff_url()

        if not self.request.htmx:
            return redirect(org_detail)

        # HTMX clients should pass ?next={{ request.path }} in the template,
        # but we can fall back to a sensible location otherwise
        next_url = self.request.GET.get("next") or org_detail
        return HttpResponseClientRedirect(next_url)

    def get_context_data(self, **kwargs):
        return super().get_context_data() | {
            "next": self.request.GET.get("next") or "",
        }

    def get_template_names(self):
        suffix = ".htmx" if self.request.htmx else ""
        template_name = f"staff/org_create{suffix}.html"

        return [template_name]


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class OrgDetail(FormView):
    form_class = OrgAddMemberForm
    template_name = "staff/org_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Org, slug=self.kwargs["slug"])

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        users = form.cleaned_data["users"]

        with transaction.atomic():
            for user in users:
                self.object.memberships.create(
                    user=user,
                    created_by=self.request.user,
                )

        return redirect(self.object.get_staff_url())

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "github_orgs": sorted(self.object.github_orgs),
            "members": self.object.members.order_by(Lower("username")),
            "org": self.object,
            "projects": self.object.projects.order_by("number", Lower("name")),
        }

    def get_form_kwargs(self):
        members = self.object.members.values_list("pk", flat=True)
        return super().get_form_kwargs() | {
            "users": User.objects.exclude(pk__in=members),
        }

    def get_initial(self):
        return super().get_initial() | {
            "users": self.object.members.values_list("pk", flat=True),
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class OrgEdit(UpdateView):
    fields = [
        "name",
        "slug",
        "logo_file",
    ]
    model = Org
    template_name = "staff/org_edit.html"

    def form_valid(self, form):
        # look up the original object from the database because the form will
        # mutation self.object under us
        old = self.get_object()

        new = form.save()

        # check changed_data here instead of comparing self.object.slug to
        # new.slug because self.object is mutated when ModelForm._post_clean
        # updates the instance it was passed.  This is because form.instance is
        # set from the passed in self.object.
        if "slug" in form.changed_data:
            new.redirects.create(
                created_by=self.request.user,
                old_url=old.get_absolute_url(),
            )

        return redirect(new.get_staff_url())


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
class OrgProjectCreate(CreateView):
    fields = ["name"]
    model = Project
    template_name = "staff/org_project_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.org = get_object_or_404(Org, slug=self.kwargs["slug"])

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        project = form.save(commit=False)
        project.created_by = self.request.user
        project.org = self.org
        project.save()

        return redirect(project.get_staff_url())

    def get_context_data(self, **kwargs):
        return super().get_context_data() | {
            "org": self.org,
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class OrgRemoveGitHubOrg(View):
    def post(self, request, *args, **kwargs):
        org = get_object_or_404(Org, slug=self.kwargs["slug"])
        name = request.POST.get("name", None)

        try:
            org.github_orgs.remove(name)
        except ValueError:
            messages.error(request, f"{name} is not assigned to {org.name}")
        else:
            org.save()
            messages.success(request, f"Removed {name} from {org.name}")

        return redirect(org.get_staff_url())


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
