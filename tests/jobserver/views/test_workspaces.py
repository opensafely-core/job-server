from unittest.mock import patch

import pytest
import responses
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.urls import reverse

from jobserver.authorization import ProjectDeveloper
from jobserver.models import JobRequest, Workspace
from jobserver.views.workspaces import (
    BaseWorkspaceDetail,
    GlobalWorkspaceDetail,
    ProjectWorkspaceDetail,
    WorkspaceArchiveToggle,
    WorkspaceCreate,
    WorkspaceLog,
    WorkspaceNotificationsToggle,
    WorkspaceReleaseView,
)

from ...factories import (
    JobFactory,
    JobRequestFactory,
    OrgFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
    WorkspaceFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_baseworkspacedetail_requires_can_run_jobs(rf):
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    with pytest.raises(NotImplementedError):
        BaseWorkspaceDetail.as_view()(request)


@pytest.mark.django_db
def test_projectworkspacedetail_redirect_to_global_view(rf):
    workspace = WorkspaceFactory()

    request = rf.get(MEANINGLESS_URL)
    response = ProjectWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()


@pytest.mark.django_db
def test_projectworkspacedetail_success(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    request = rf.get(MEANINGLESS_URL)
    request.user = user
    response = ProjectWorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["user_can_run_jobs"]


@pytest.mark.django_db
def test_projectworkspacedetail_unknown_workspace(rf):
    request = rf.get(MEANINGLESS_URL)
    response = ProjectWorkspaceDetail.as_view()(
        request,
        org_slug="",
        project_slug="",
        workspace_slug="",
    )

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
@responses.activate
def test_workspacearchivetoggle_success(rf):
    workspace = WorkspaceFactory(is_archived=False)
    user = UserFactory()

    request = rf.post(MEANINGLESS_URL, {"is_archived": "True"})
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = WorkspaceArchiveToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == "/"

    workspace.refresh_from_db()
    assert workspace.is_archived


@pytest.mark.django_db
@responses.activate
def test_workspacearchivetoggle_unauthorized(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = WorkspaceArchiveToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
@responses.activate
def test_workspacecreate_get_success(rf):
    user = UserFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    with patch(
        "jobserver.views.workspaces.get_repos_with_branches", new=lambda *args: []
    ):
        response = WorkspaceCreate.as_view()(request)

    assert response.status_code == 200
    assert response.context_data["repos_with_branches"] == []


@pytest.mark.django_db
@responses.activate
def test_workspacecreate_post_success(rf):
    user = UserFactory()

    data = {
        "name": "Test",
        "repo": "test",
        "branch": "test",
        "db": "slice",
    }

    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    repos = [{"name": "Test", "url": "test", "branches": ["test"]}]
    with patch(
        "jobserver.views.workspaces.get_repos_with_branches", new=lambda *args: repos
    ):
        response = WorkspaceCreate.as_view()(request)

    assert response.status_code == 302

    workspace = Workspace.objects.first()
    assert response.url == reverse("workspace-detail", kwargs={"name": workspace.name})
    assert workspace.created_by == user


@pytest.mark.django_db
@responses.activate
def test_workspacecreate_unauthorized(rf):
    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = WorkspaceCreate.as_view()(request)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
def test_workspacedetail_logged_out(rf):
    workspace = WorkspaceFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()

    with patch(
        "jobserver.views.workspaces.get_actions", autospec=True
    ) as mocked_get_actions:
        response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    mocked_get_actions.assert_not_called()

    assert response.status_code == 200

    assert response.context_data["actions"] == []
    assert response.context_data["branch"] == workspace.branch


@pytest.mark.django_db
def test_workspacedetail_project_yaml_errors(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = user

    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ), patch(
        "jobserver.views.workspaces.get_project",
        side_effect=Exception("test error"),
        autospec=True,
    ):
        response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 200

    assert response.context_data["actions"] == []
    assert response.context_data["actions_error"] == "test error"


@pytest.mark.django_db
def test_workspacedetail_get_success(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = user

    dummy_yaml = """
    actions:
      twiddle:
    """
    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ), patch("jobserver.views.workspaces.get_project", new=lambda *args: dummy_yaml):
        response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": [], "status": "-"},
        {"name": "run_all", "needs": ["twiddle"], "status": "-"},
    ]
    assert response.context_data["branch"] == workspace.branch


@pytest.mark.django_db
def test_workspacedetail_post_archived_workspace(rf):
    workspace = WorkspaceFactory(is_archived=True)

    request = rf.post(MEANINGLESS_URL)
    request.session = "session"
    request._messages = FallbackStorage(request)
    request.user = UserFactory()

    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ), patch("jobserver.views.workspaces.get_actions", return_value=[], autospec=True):
        response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()


@pytest.mark.django_db
def test_workspacedetail_post_success(rf, monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp")

    workspace = WorkspaceFactory()
    user = UserFactory()

    data = {
        "requested_actions": ["twiddle"],
        "callback_url": "test",
    }

    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    dummy_yaml = """
    actions:
      twiddle:
    """
    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ), patch(
        "jobserver.views.workspaces.get_project", new=lambda *args: dummy_yaml
    ), patch(
        "jobserver.views.workspaces.get_branch_sha", new=lambda r, b: "abc123"
    ):
        response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == reverse("workspace-logs", kwargs={"name": workspace.name})

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend.name == "tpp"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert not job_request.jobs.exists()


@pytest.mark.django_db
def test_workspacedetail_post_with_notifications_default(rf, monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp")

    workspace = WorkspaceFactory(should_notify=True)
    user = UserFactory()

    data = {
        "requested_actions": ["twiddle"],
        "callback_url": "test",
        "will_notify": "True",
    }

    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    dummy_yaml = """
    actions:
      twiddle:
    """
    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ), patch(
        "jobserver.views.workspaces.get_project", new=lambda *args: dummy_yaml
    ), patch(
        "jobserver.views.workspaces.get_branch_sha", new=lambda r, b: "abc123"
    ):
        response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == reverse("workspace-logs", kwargs={"name": workspace.name})

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend.name == "tpp"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert job_request.will_notify


@pytest.mark.django_db
def test_workspacedetail_post_with_notifications_override(rf, monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp")

    workspace = WorkspaceFactory(should_notify=True)
    user = UserFactory()

    data = {
        "requested_actions": ["twiddle"],
        "callback_url": "test",
        "will_notify": "False",
    }

    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    dummy_yaml = """
    actions:
      twiddle:
    """
    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ), patch(
        "jobserver.views.workspaces.get_project", new=lambda *args: dummy_yaml
    ), patch(
        "jobserver.views.workspaces.get_branch_sha", new=lambda r, b: "abc123"
    ):
        response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == reverse("workspace-logs", kwargs={"name": workspace.name})

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend.name == "tpp"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert not job_request.will_notify
    assert not job_request.jobs.exists()


@pytest.mark.django_db
def test_workspacedetail_post_success_with_superuser(rf, monkeypatch, superuser):
    monkeypatch.setenv("BACKENDS", "tpp,emis")

    workspace = WorkspaceFactory()
    user = superuser

    data = {
        "backend": "emis",
        "requested_actions": ["twiddle"],
        "callback_url": "test",
    }

    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    dummy_yaml = """
    actions:
      twiddle:
    """
    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ), patch(
        "jobserver.views.workspaces.get_project", new=lambda *args: dummy_yaml
    ), patch(
        "jobserver.views.workspaces.get_branch_sha", new=lambda r, b: "abc123"
    ):
        response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == reverse("workspace-logs", kwargs={"name": workspace.name})

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend.name == "emis"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert not job_request.jobs.exists()


@pytest.mark.django_db
def test_workspacedetail_redirects_with_project_url(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    request = rf.get(MEANINGLESS_URL)
    response = GlobalWorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "project-workspace-detail",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspacedetail_unknown_workspace(rf):
    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = GlobalWorkspaceDetail.as_view()(request, name="test")

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_workspacedetail_get_with_authenticated_user(rf):
    """
    Check GlobalWorkspaceDetail renders the controls for Archiving, Notifications,
    and selecting Actions for authenticated Users.
    """
    workspace = WorkspaceFactory(is_archived=False)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=False, roles=[])

    dummy_yaml = """
    actions:
      twiddle:
    """
    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ), patch("jobserver.views.workspaces.get_project", new=lambda *args: dummy_yaml):
        response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert "Archive" in response.rendered_content
    assert "Turn Notifications" in response.rendered_content
    assert "twiddle" in response.rendered_content
    assert "Pick a backend to run your Jobs in" not in response.rendered_content


@pytest.mark.django_db
def test_workspacedetail_get_with_superuser(rf, superuser):
    """Check GlobalWorkspaceDetail renders the Backend radio buttons for superusers"""
    workspace = WorkspaceFactory(is_archived=False)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    dummy_yaml = """
    actions:
      twiddle:
    """
    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ), patch("jobserver.views.workspaces.get_project", new=lambda *args: dummy_yaml):
        response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert "Pick a backend to run your Jobs in" in response.rendered_content


@pytest.mark.django_db
def test_workspacedetail_get_with_unauthenticated_user(rf):
    """
    Check GlobalWorkspaceDetail does not render the controls for Archiving,
    Notifications, and selecting Actions for unauthenticated Users.
    """
    workspace = WorkspaceFactory(is_archived=False)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()
    response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert "Archive" not in response.rendered_content
    assert "Turn Notifications" not in response.rendered_content
    assert "twiddle" not in response.rendered_content


@pytest.mark.django_db
def test_workspacelog_search_by_action(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    job_request1 = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request1, action="run")

    job_request2 = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request2, action="leap")

    # Build a RequestFactory instance
    request = rf.get("/?q=run")
    request.user = user

    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ):
        response = WorkspaceLog.as_view()(request, name=workspace.name)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request1


@pytest.mark.django_db
def test_workspacelog_search_by_id(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    JobFactory(job_request=JobRequestFactory())

    job_request2 = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request2, id=99)

    # Build a RequestFactory instance
    request = rf.get("/?q=99")
    request.user = user

    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ):
        response = WorkspaceLog.as_view()(request, name=workspace.name)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request2


@pytest.mark.django_db
def test_workspacelog_success(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()
    job_request = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = user

    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ):
        response = WorkspaceLog.as_view()(request, name=workspace.name)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_workspacelog_unknown_workspace(rf):
    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = WorkspaceLog.as_view()(request, name="test")

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_workspacelog_with_authenticated_user(rf):
    """
    Check WorkspaceLog renders the Add Job button for authenticated Users
    """
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    with patch(
        "jobserver.views.workspaces.can_run_jobs", return_value=True, autospec=True
    ):
        response = WorkspaceLog.as_view()(request, name=workspace.name)

    assert response.status_code == 200
    assert "Add Job" in response.rendered_content


@pytest.mark.django_db
def test_workspacelog_with_unauthenticated_user(rf):
    """
    Check WorkspaceLog renders the Add Job button for authenticated Users
    """
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()
    response = WorkspaceLog.as_view()(request, name=workspace.name)

    assert response.status_code == 200
    assert "Add Job" not in response.rendered_content


@pytest.mark.django_db
@responses.activate
def test_workspacenotificationstoggle_success(rf):
    user = UserFactory()
    workspace = WorkspaceFactory(should_notify=True)

    request = rf.post(MEANINGLESS_URL, {"should_notify": ""})
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = WorkspaceNotificationsToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    workspace.refresh_from_db()

    assert not workspace.should_notify


@pytest.mark.django_db
@responses.activate
def test_workspacenotificationstoggle_unauthorized(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    request = rf.post(MEANINGLESS_URL, {"should_notify": ""})
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = WorkspaceNotificationsToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
@responses.activate
def test_workspacenotificationstoggle_unknown_workspace(rf):
    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    with pytest.raises(Http404):
        WorkspaceNotificationsToggle.as_view()(request, name="test")


@pytest.mark.django_db
@responses.activate
def test_workspacerelease_unauthorized(rf):
    user = UserFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = WorkspaceReleaseView.as_view()(request)
    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"
