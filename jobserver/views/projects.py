from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views.generic import CreateView, DetailView, UpdateView, View
from sentry_sdk import capture_exception

from ..authorization import has_permission, roles_for
from ..authorization.decorators import require_superuser
from ..emails import send_project_invite_email
from ..forms import (
    ProjectCreateForm,
    ProjectInvitationForm,
    ProjectMembershipForm,
    ResearcherFormSet,
)
from ..models import Org, Project, ProjectInvitation, ProjectMembership, User


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

        invite.create_membership()

        return redirect(invite.project)


@method_decorator(require_superuser, name="dispatch")
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
            "manage_project_members",
            project=invite.project,
        )
        if not can_manage_members:
            raise Http404

        invite.delete()

        return redirect(invite.project.get_settings_url())


@method_decorator(require_superuser, name="dispatch")
class ProjectCreate(CreateView):
    form_class = ProjectCreateForm
    model = Project
    template_name = "project_create.html"

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
        can_manage_workspaces = has_permission(
            self.request.user,
            "manage_project_workspaces",
            project=self.object,
        )
        can_manage_members = has_permission(
            self.request.user,
            "manage_project_members",
            project=self.object,
        )

        context = super().get_context_data(**kwargs)
        context["can_manage_workspaces"] = can_manage_workspaces
        context["can_manage_members"] = can_manage_members
        context["workspaces"] = self.object.workspaces.order_by("name")
        return context


class ProjectDisconnectWorkspace(View):
    def post(self, request, *args, **kwargs):
        """A transitional view to help with migrating Workspaces under Projects"""
        project = get_object_or_404(
            Project,
            org__slug=self.kwargs["org_slug"],
            slug=self.kwargs["project_slug"],
        )

        can_manage_workspaces = has_permission(
            request.user,
            "manage_project_workspaces",
            project=project,
        )
        if not can_manage_workspaces:
            raise Http404

        workspace_id = request.POST.get("id")
        if not workspace_id:
            return redirect(project)

        project.workspaces.filter(pk=workspace_id).update(project=None)

        return redirect(project)


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
            "manage_project_members",
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

        members = self.project.members.select_related("user").order_by("user__username")
        invitations = (
            self.project.invitations.filter(membership=None)
            .select_related("user")
            .order_by("user__username")
        )

        context = super().get_context_data(**kwargs)
        context["can_manage_members"] = self.can_manage_members
        context["invitations"] = invitations
        context["members"] = members
        context["project"] = self.project
        return context

    def get_form_kwargs(self, **kwargs):
        # memberships do not guarantee a matching invitation and vice versa so
        # look them all up and get a unique list
        user_ids = set(
            [
                *self.project.members.values_list("user_id", flat=True),
                *self.project.invitations.values_list("user_id", flat=True),
            ]
        )
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
            "manage_project_members",
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


@method_decorator(require_superuser, name="dispatch")
class ProjectRemoveMember(View):
    model = ProjectMembership

    def post(self, request, *args, **kwargs):
        try:
            membership = ProjectMembership.objects.select_related("project").get(
                project__org__slug=self.kwargs["org_slug"],
                project__slug=self.kwargs["project_slug"],
                user__username=self.request.POST.get("username"),
            )
        except ProjectMembership.DoesNotExist:
            raise Http404

        can_manage_members = has_permission(
            self.request.user,
            "manage_project_members",
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
            "manage_project_members",
            project=self.project,
        )
        if not self.can_manage_members:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        members = self.project.members.select_related("user").order_by("user__username")
        invitations = (
            self.project.invitations.filter(membership=None)
            .select_related("user")
            .order_by("user__username")
        )

        context = super().get_context_data(**kwargs)
        context["can_manage_members"] = self.can_manage_members
        context["invitations"] = invitations
        context["members"] = members
        context["project"] = self.project
        return context
