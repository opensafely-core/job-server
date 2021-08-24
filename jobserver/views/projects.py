from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views.generic import CreateView, DetailView, UpdateView, View
from furl import furl
from sentry_sdk import capture_exception

from ..authorization import (
    CoreDeveloper,
    ProjectDeveloper,
    has_permission,
    has_role,
    roles_for,
)
from ..authorization.decorators import require_role
from ..emails import send_project_invite_email
from ..forms import (
    ProjectInvitationForm,
    ProjectMembershipForm,
    ProjectOnboardingCreateForm,
    ResearcherFormSet,
)
from ..github import get_repo_is_private
from ..models import Org, Project, ProjectInvitation, ProjectMembership, Snapshot, User


@method_decorator(login_required, name="dispatch")
class ProjectAcceptInvite(View):
    def get(self, request, *args, **kwargs):
        signed_pk = self.kwargs["signed_pk"]

        try:
            invite = ProjectInvitation.get_from_signed_pk(signed_pk)
        except (ProjectInvitation.DoesNotExist, signing.BadSignature):
            raise Http404

        if request.user != invite.user:
            messages.error(
                request,
                "Only the User who was invited may accept an invite.",
            )
            return redirect("/")

        if invite.membership:
            return redirect(invite.project)

        invite.create_membership()

        return redirect(invite.project)


class ProjectCancelInvite(View):
    def post(self, request, *args, **kwargs):
        invite = get_object_or_404(
            ProjectInvitation,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            pk=self.request.POST.get("invite_pk"),
        )

        can_manage_members = has_permission(
            request.user,
            "project_membership_edit",
            project=invite.project,
        )
        if not can_manage_members:
            raise Http404

        invite.delete()

        return redirect(invite.project.get_settings_url())


class ProjectCreate(CreateView):
    fields = ["name"]
    model = Project
    template_name = "project_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.org = get_object_or_404(Org, slug=self.kwargs["org_slug"])

        if self.org.slug not in ["datalab", "graphnet", "lshtm"]:
            # Only DataLab and LSHTM have blanket approval, all other orgs must
            # go through the onboarding process to get approval for their
            # projects.
            return redirect("project-onboarding", org_slug=self.org.slug)

        if request.user not in self.org.members.all():
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic()
    def form_valid(self, form):
        project = form.save(commit=False)
        project.org = self.org
        project.save()

        project.memberships.create(
            user=self.request.user,
            roles=[ProjectDeveloper],
        )

        return redirect(project)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            org=self.org,
            **kwargs,
        )


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectEdit(UpdateView):
    """
    Staff-only view for general Project editing

    TODO: move to a staff-only area
    """

    fields = ["uses_new_release_flow"]
    model = Project
    slug_url_kwarg = "project_slug"
    template_name = "project_edit.html"


class ProjectOnboardingCreate(CreateView):
    form_class = ProjectOnboardingCreateForm
    model = Project
    template_name = "project_onboarding_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.org = get_object_or_404(Org, slug=self.kwargs["org_slug"])

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = None
        researcher_formset = ResearcherFormSet(prefix="researcher")
        return self.render_to_response(
            self.get_context_data(researcher_formset=researcher_formset)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["org"] = self.org
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = None

        form = self.get_form()
        researcher_formset = ResearcherFormSet(request.POST, prefix="researcher")

        form_valid = form.is_valid()
        formset_valid = researcher_formset.is_valid()
        if not (form_valid and formset_valid):
            return self.render_to_response(
                self.get_context_data(researcher_formset=researcher_formset)
            )

        project = form.save(commit=False)
        project.org = self.org
        project.save()

        researchers = researcher_formset.save()
        project.researcher_registrations.add(*researchers)

        return redirect(project)


class ProjectDetail(DetailView):
    template_name = "project_detail.html"

    def get_object(self):
        return get_object_or_404(
            Project,
            slug=self.kwargs["project_slug"],
            org__slug=self.kwargs["org_slug"],
        )

    def get_context_data(self, **kwargs):
        can_create_workspaces = has_permission(
            self.request.user,
            "workspace_create",
            project=self.object,
        )
        can_manage_members = has_permission(
            self.request.user,
            "project_membership_edit",
            project=self.object,
        )
        can_use_releases = has_role(self.request.user, CoreDeveloper)
        can_change_release_process = has_role(self.request.user, CoreDeveloper)

        workspaces = self.object.workspaces.order_by("name")

        repos = sorted(set(workspaces.values_list("repo", flat=True)))

        return super().get_context_data(**kwargs) | {
            "can_create_workspaces": can_create_workspaces,
            "can_change_release_process": can_change_release_process,
            "can_manage_members": can_manage_members,
            "can_use_releases": can_use_releases,
            "outputs": self.get_outputs(workspaces),
            "repos": list(self.get_repos(repos)),
            "workspaces": workspaces,
        }

    def get_outputs(self, workspaces):
        """
        Builds up a QuerySet of Snapshots (outputs) for the page

        We only want to show the most recent published Snapshot for each
        Workspace.
        """
        # build a Subquery to get the PK for the most recently published
        # Snapshot for each Workspace
        latest_snapshot_qs = (
            Snapshot.objects.filter(workspace_id=OuterRef("id"))
            .exclude(published_at=None)
            .order_by("-published_at")
            .values("pk")[:1]
        )

        # annotate the subquery onto the Workspace QuerySet
        workspaces = workspaces.annotate(latest_snapshot=Subquery(latest_snapshot_qs))

        # build the QuerySet of Snapshots from the PKs annotated onto each Workspace
        snapshot_pks = workspaces.exclude(latest_snapshot=None).values_list(
            "latest_snapshot", flat=True
        )

        return Snapshot.objects.filter(pk__in=snapshot_pks).order_by("-published_at")

    def get_repos(self, repo_urls):
        for url in repo_urls:
            f = furl(url)

            yield {
                "name": f.path.segments[1],
                "url": url,
                "is_private": get_repo_is_private(*f.path.segments),
            }


class ProjectInvitationCreate(CreateView):
    form_class = ProjectInvitationForm
    model = ProjectInvitation
    template_name = "project_invitation_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            Project,
            org__slug=self.kwargs["org_slug"],
            slug=self.kwargs["project_slug"],
        )

        self.can_manage_members = has_permission(
            self.request.user,
            "project_membership_edit",
            project=self.project,
        )
        if not self.can_manage_members:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        roles = form.cleaned_data["roles"]
        user_pks = form.cleaned_data["users"]

        failed_to_invite = []

        users = User.objects.filter(pk__in=user_pks)
        for user in users:
            try:
                with transaction.atomic():
                    invite = ProjectInvitation.objects.create(
                        created_by=self.request.user,
                        project=self.project,
                        user=user,
                        roles=roles,
                    )
                    send_project_invite_email(
                        user.notifications_email, self.project, invite
                    )
            except Exception as e:
                capture_exception(e)
                failed_to_invite.append(user)

        if failed_to_invite:
            # tell the user about each failed invite in a single message
            users = [f"<li>{escape(u.username)}</li>" for u in failed_to_invite]
            users = f"<ul>{''.join(users)}</ul>"

            messages.error(
                self.request,
                f"<p>Failed to invite {len(failed_to_invite)} User(s):</p>{users}<p>Please try again.</p>",
            )

        return redirect(
            "project-settings",
            org_slug=self.project.org.slug,
            project_slug=self.project.slug,
        )

    def get_context_data(self, **kwargs):

        invitations = (
            self.project.invitations.filter(membership=None)
            .select_related("user")
            .order_by("user__username")
        )

        context = super().get_context_data(**kwargs)
        context["can_manage_members"] = self.can_manage_members
        context["invitations"] = invitations
        context["project"] = self.project
        return context

    def get_form_kwargs(self, **kwargs):
        # memberships do not guarantee a matching invitation and vice versa so
        # look them all up and get a unique list
        user_ids = {
            *self.project.memberships.values_list("user_id", flat=True),
            *self.project.invitations.values_list("user_id", flat=True),
        }
        users = User.objects.exclude(pk__in=user_ids).order_by("username")

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs["available_roles"] = roles_for(ProjectInvitation)
        kwargs["users"] = users

        # we're not using a ModelForm so make sure there's no instance for it
        # to deal with
        del kwargs["instance"]

        return kwargs


class ProjectMembershipEdit(UpdateView):
    context_object_name = "membership"
    form_class = ProjectMembershipForm
    model = ProjectMembership
    template_name = "project_membership_edit.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            Project,
            org__slug=self.kwargs["org_slug"],
            slug=self.kwargs["project_slug"],
        )

        self.can_manage_members = has_permission(
            self.request.user,
            "project_membership_edit",
            project=self.project,
        )

        if not self.can_manage_members:
            return redirect(self.project.get_settings_url())

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object.roles = form.cleaned_data["roles"]
        self.object.save()

        return redirect(self.project.get_settings_url())

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
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            pk=self.kwargs["pk"],
        )


class ProjectMembershipRemove(View):
    model = ProjectMembership

    def post(self, request, *args, **kwargs):
        try:
            membership = ProjectMembership.objects.select_related("project").get(
                project__org__slug=self.kwargs["org_slug"],
                project__slug=self.kwargs["project_slug"],
                pk=self.request.POST.get("member_pk"),
            )
        except ProjectMembership.DoesNotExist:
            raise Http404

        can_manage_members = has_permission(
            self.request.user,
            "project_membership_edit",
            project=membership.project,
        )
        if can_manage_members:
            membership.delete()
        else:
            messages.error(
                request, "You do not have permission to remove Project members."
            )

        return redirect(membership.project.get_settings_url())


class ProjectSettings(UpdateView):
    fields = ["name"]
    model = Project
    slug_url_kwarg = "project_slug"
    template_name = "project_settings.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            Project,
            org__slug=self.kwargs["org_slug"],
            slug=self.kwargs["project_slug"],
        )

        self.can_manage_members = has_permission(
            self.request.user,
            "project_membership_edit",
            project=self.project,
        )
        if not self.can_manage_members:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        memberships = self.project.memberships.select_related("user").order_by(
            "user__username"
        )
        invitations = (
            self.project.invitations.filter(membership=None)
            .select_related("user")
            .order_by("user__username")
        )

        context = super().get_context_data(**kwargs)
        context["can_manage_members"] = self.can_manage_members
        context["invitations"] = invitations
        context["memberships"] = memberships
        context["project"] = self.project
        return context
