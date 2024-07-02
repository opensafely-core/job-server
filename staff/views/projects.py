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
from markdown import markdown
from zen_queries import TemplateResponse as zTemplateResponse
from zen_queries import fetch

from applications.models import Application
from interactive.commands import create_repo, create_workspace
from jobserver import html_utils
from jobserver.auditing.presenters.lookup import get_presenter
from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.authorization.utils import roles_for
from jobserver.commands import project_members as members
from jobserver.commands import projects
from jobserver.github import GitHubError, _get_github_api
from jobserver.models import AuditableEvent, Org, Project, ProjectMembership, User

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
    template_name = "staff/project/membership_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=self.kwargs["slug"])

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic()
    def form_valid(self, form):
        for user in form.cleaned_data["users"]:
            members.add(
                project=self.project,
                user=user,
                roles=form.cleaned_data["roles"],
                by=self.request.user,
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
            "users": User.objects.exclude(pk__in=members).order_by_name(),
        }

    def get_initial(self):
        return super().get_initial() | {
            "users": self.project.members.values_list("pk", flat=True),
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectAuditLog(ListView):
    paginate_by = 25
    template_name = "staff/project/audit_log.html"
    response_class = zTemplateResponse

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=self.kwargs["slug"])

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        events = self.get_queryset()
        presentable_events = [get_presenter(e)(event=e) for e in events]

        types = AuditableEvent.get_types(prefix="project_member")

        # Note: we're passing in presentable_events here to override the use of
        # self.object_list which is an iterable of AuditableEvents, but we're
        # going to be using presentable_events in the template so we want to
        # paginate on those instead.
        return super().get_context_data(object_list=presentable_events, **kwargs) | {
            "events": presentable_events,
            "project": self.project,
            "types": types,
        }

    def get_queryset(self):
        qs = AuditableEvent.objects.filter(
            parent_model=Project._meta.label, parent_id=str(self.project.pk)
        ).order_by("-created_at", "-pk")

        if types := self.request.GET.getlist("types"):
            qs = qs.filter(type__in=types)

        return fetch(qs.distinct())


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectCreate(CreateView):
    form_class = ProjectCreateForm
    get_github_api = staticmethod(_get_github_api)

    def form_valid(self, form):
        # wrap the transaction in a try so it can rollback when that fires
        try:
            with transaction.atomic():
                project = projects.add(**form.cleaned_data, by=self.request.user)

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
        template_name = f"staff/project/create{suffix}.html"

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
            "orgs": self.object.orgs.order_by(Lower("name")),
            "redirects": self.object.redirects.order_by("old_url"),
            "status_description_html": html_utils.clean_html(
                markdown(self.object.status_description)
            ),
            "workspaces": self.object.workspaces.order_by("name"),
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectEdit(UpdateView):
    form_class = ProjectEditForm
    model = Project
    template_name = "staff/project/edit.html"

    @transaction.atomic()
    def form_valid(self, form):
        new = projects.edit(old=self.get_object(), form=form, by=self.request.user)

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
    template_name = "staff/project/link_application.html"

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
            "orgs": Org.objects.order_by(Lower("name")),
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

        if orgs := self.request.GET.getlist("orgs"):
            qs = qs.filter(orgs__slug__in=orgs)

        return qs.distinct()


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectMembershipEdit(UpdateView):
    context_object_name = "membership"
    form_class = ProjectMembershipForm
    model = ProjectMembership
    template_name = "staff/project/membership_edit.html"

    def form_valid(self, form):
        members.update_roles(
            membership=self.object,
            by=self.request.user,
            roles=form.cleaned_data["roles"],
        )

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

        members.remove(membership=membership, by=self.request.user)

        messages.success(
            request,
            f"Removed {membership.user.username} from {membership.project.title}",
        )

        return redirect(
            get_next_url(self.request.GET, membership.project.get_staff_url())
        )
