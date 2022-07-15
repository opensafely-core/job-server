import concurrent
import operator

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views.generic import CreateView, UpdateView, View
from furl import furl
from sentry_sdk import capture_exception

from ..authorization import has_permission, roles_for
from ..emails import send_project_invite_email
from ..forms import ProjectInvitationForm, ProjectMembershipForm
from ..github import _get_github_api
from ..models import Project, ProjectInvitation, ProjectMembership, Snapshot, User


# Create a global threadpool for getting repos.  This lets us have a single
# pool across all requests and saves the overhead from setting up threads on
# each request.
repo_thread_pool = concurrent.futures.ThreadPoolExecutor(thread_name_prefix="get_repo")


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


class ProjectDetail(View):
    get_github_api = staticmethod(_get_github_api)

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            slug=self.kwargs["project_slug"],
            org__slug=self.kwargs["org_slug"],
        )

        can_create_workspaces = has_permission(
            request.user, "workspace_create", project=project
        )
        can_manage_members = has_permission(
            request.user, "project_membership_edit", project=project
        )

        workspaces = project.workspaces.order_by("is_archived", "name")

        repos = set(workspaces.values_list("repo", flat=True))

        context = {
            "can_create_workspaces": can_create_workspaces,
            "can_manage_members": can_manage_members,
            "outputs": self.get_outputs(workspaces),
            "project": project,
            "repos": list(
                sorted(self.iter_repos(repos), key=operator.itemgetter("name"))
            ),
            "workspaces": workspaces,
        }

        return TemplateResponse(request, "project_detail.html", context=context)

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

    def iter_repos(self, repo_urls):
        def get_repo(url):
            f = furl(url)

            try:
                is_private = self.get_github_api().get_repo_is_private(*f.path.segments)
            except requests.HTTPError:
                is_private = None

            return {
                "name": f.path.segments[1],
                "url": url,
                "is_private": is_private,
            }

        # use the threadpool to parallelise the repo requests
        yield from repo_thread_pool.map(get_repo, repo_urls, timeout=30)


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
