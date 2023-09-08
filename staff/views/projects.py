from django.contrib import messages
from django.db import transaction
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
    View,
)
from django_htmx.http import HttpResponseClientRedirect
from furl import furl

from applications.models import Application
from interactive.commands import create_repo, create_workspace
from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.authorization.utils import roles_for
from jobserver.github import GitHubError, _get_github_api
from jobserver.models import Org, Project, ProjectMembership, User

from ..forms import (
    ProjectAddMemberForm,
    ProjectCreateForm,
    ProjectEditForm,
    ProjectLinkApplicationForm,
    ProjectMembershipForm,
)
from ..htmx_tools import get_redirect_url
from ..querystring_tools import get_next_url
from .qwargs_tools import qwargs


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectAddMember(FormView):
    form_class = ProjectAddMemberForm
    template_name = "staff/project_membership_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=self.kwargs["slug"])

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        roles = form.cleaned_data["roles"]
        users = form.cleaned_data["users"]

        with transaction.atomic():
            for user in users:
                self.project.memberships.create(
                    user=user,
                    created_by=self.request.user,
                    roles=roles,
                )

        return redirect(self.project.get_staff_url())

    def get_context_data(self, **kwargs):
        f = furl(reverse("staff:user-create"))
        f.args.update(
            {
                "project-slug": self.project.slug,
                "next": self.project.get_staff_url(),
            }
        )

        return super().get_context_data(**kwargs) | {
            "project": self.project,
            "user_create_url": f.url,
        }

    def get_form_kwargs(self):
        members = self.project.members.values_list("pk", flat=True)
        return super().get_form_kwargs() | {
            "available_roles": roles_for(ProjectMembership),
            "users": User.objects.exclude(pk__in=members),
        }

    def get_initial(self):
        return super().get_initial() | {
            "users": self.project.members.values_list("pk", flat=True),
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectCreate(CreateView):
    form_class = ProjectCreateForm
    get_github_api = staticmethod(_get_github_api)

    def form_valid(self, form):
        # wrap the transaction in a try so it can rollback when that fires
        try:
            with transaction.atomic():
                project = Project.objects.create(
                    **form.cleaned_data,
                    created_by=self.request.user,
                    updated_by=self.request.user,
                )

                # make sure the relevant interactive repo exists on GitHub
                repo_url = create_repo(
                    name=project.interactive_slug,
                    get_github_api=self.get_github_api,
                )

                # make sure the expected workspace exists
                create_workspace(
                    creator=self.request.user,
                    project=project,
                    repo_url=repo_url,
                )
        except GitHubError:
            form.add_error(
                None,
                "An error occurred when trying to create the required Repo on GitHub",
            )
            return self.form_invalid(form)

        project_detail = project.get_staff_url()

        if not self.request.htmx:
            return redirect(project_detail)

        url = get_redirect_url(
            self.request.GET,
            project_detail,
            {"project-slug": project.slug},
        )
        return HttpResponseClientRedirect(url)

    def get_context_data(self, **kwargs):
        f = furl(reverse("staff:project-create"))

        # set the query args of the furl object, f, with the query args on
        # the current request.
        f.args.update(self.request.GET)

        return super().get_context_data(**kwargs) | {
            "application_url_attributes": {"type": "url"},
            "number_attributes": {
                "inputmode": "numeric",
                "pattern": "[0-9]*",
            },
            "post_url": f.url,
        }

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)

        # ProjectCreateForm isn't a ModelForm so don't pass instance to it
        del kwargs["instance"]

        return kwargs

    def get_template_names(self):
        suffix = ".htmx" if self.request.htmx else ""
        template_name = f"staff/project_create{suffix}.html"

        return [template_name]


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectDetail(DetailView):
    model = Project
    template_name = "staff/project/detail.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "application": self.object.applications.first(),
            "memberships": self.object.memberships.select_related("user").order_by(
                Lower("user__username")
            ),
            "redirects": self.object.redirects.order_by("old_url"),
            "workspaces": self.object.workspaces.order_by("name"),
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectEdit(UpdateView):
    form_class = ProjectEditForm
    model = Project
    template_name = "staff/project_edit.html"

    @transaction.atomic()
    def form_valid(self, form):
        # look up the original object from the database because the form will
        # mutation self.object under us
        old = self.get_object()

        new = form.save(commit=False)
        new.updated_by = self.request.user
        new.save()

        # check changed_data here instead of comparing self.object.project to
        # new.project because self.object is mutated when ModelForm._post_clean
        # updates the instance it was passed.  This is because form.instance is
        # set from the passed in self.object.
        if {"org", "slug"} & set(form.changed_data):
            new.redirects.create(
                created_by=self.request.user,
                old_url=old.get_absolute_url(),
            )

        return redirect(new.get_staff_url())

    def get_context_data(self, **kwargs):
        # we don't have a nice way to override the type of text input
        # components yet so doing this here is a bit of a hack because we can't
        # construct dicts in a template
        return super().get_context_data(**kwargs) | {
            "application_url_attributes": {"type": "url"},
            "number_attributes": {"type": "number"},
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectLinkApplication(UpdateView):
    form_class = ProjectLinkApplicationForm
    model = Project
    template_name = "staff/project_link_application.html"

    def form_valid(self, form):
        application = form.cleaned_data["application"]

        self.object.applications.add(application)
        self.object.save()

        return redirect(self.object.get_staff_url())

    def get_context_data(self, **kwargs):
        # get applications that we can consider done, or at least not clearly
        # not-done
        ignored_statuses = [
            Application.Statuses.ONGOING,
            Application.Statuses.REJECTED,
        ]
        applications = (
            Application.objects.filter(project=None)
            .exclude(status__in=ignored_statuses)
            .select_related("created_by")
            .order_by("-created_at")
        )

        return super().get_context_data(**kwargs) | {
            "applications": applications,
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectList(ListView):
    queryset = Project.objects.order_by("-number", Lower("name"))
    paginate_by = 25
    template_name = "staff/project/list.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "orgs": Org.objects.order_by("name"),
            "q": self.request.GET.get("q", ""),
        }

    def get_queryset(self):
        qs = super().get_queryset()

        if q := self.request.GET.get("q"):
            fields = [
                "name",
                "number",
            ]
            qs = qs.filter(qwargs(fields, q))

        org = self.request.GET.get("org")
        if org:
            qs = qs.filter(org__slug=org)
        return qs


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectMembershipEdit(UpdateView):
    context_object_name = "membership"
    form_class = ProjectMembershipForm
    model = ProjectMembership
    template_name = "staff/project_membership_edit.html"

    def form_valid(self, form):
        self.object.roles = form.cleaned_data["roles"]
        self.object.save()

        return redirect(
            get_next_url(self.request.GET, self.object.project.get_staff_url())
        )

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)

        # ProjectMembershipForm isn't a ModelForm so don't pass instance to it
        del kwargs["instance"]

        kwargs["available_roles"] = roles_for(ProjectMembership)

        return kwargs

    def get_initial(self):
        return super().get_initial() | {
            "roles": self.object.roles,
        }

    def get_object(self):
        return get_object_or_404(
            ProjectMembership,
            project__slug=self.kwargs["slug"],
            pk=self.kwargs["pk"],
        )


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectMembershipRemove(View):
    def post(self, request, *args, **kwargs):
        membership = get_object_or_404(
            ProjectMembership, project__slug=self.kwargs["slug"], pk=self.kwargs["pk"]
        )

        membership.delete()
        messages.success(
            request,
            f"Removed {membership.user.username} from {membership.project.title}",
        )

        return redirect(
            get_next_url(self.request.GET, membership.project.get_staff_url())
        )
