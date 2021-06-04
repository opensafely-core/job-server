import pytest
import responses
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.urls import reverse

from jobserver.authorization import ProjectDeveloper
from jobserver.models import Backend, JobRequest, Workspace
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
    BackendMembershipFactory,
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
def test_projectworkspacedetail_success(rf, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

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
def test_workspacearchivetoggle_success(rf, user):
    workspace = WorkspaceFactory(is_archived=False)

    request = rf.post(MEANINGLESS_URL, {"is_archived": "True"})
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = WorkspaceArchiveToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == "/"

    workspace.refresh_from_db()
    assert workspace.is_archived


@pytest.mark.django_db
@responses.activate
def test_workspacearchivetoggle_unauthorized(rf, user):
    workspace = WorkspaceFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = WorkspaceArchiveToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
@responses.activate
def test_workspacecreate_get_success(rf, mocker, user):
    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    mocker.patch(
        "jobserver.views.workspaces.get_repos_with_branches",
        autospec=True,
        return_value=[],
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = WorkspaceCreate.as_view()(request)

    assert response.status_code == 200
    assert response.context_data["repos_with_branches"] == []


@pytest.mark.django_db
@responses.activate
def test_workspacecreate_post_success(rf, mocker, user):
    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    mocker.patch(
        "jobserver.views.workspaces.get_repos_with_branches",
        autospec=True,
        return_value=[{"name": "Test", "url": "test", "branches": ["test"]}],
    )

    data = {
        "name": "Test",
        "repo": "test",
        "branch": "test",
        "db": "slice",
    }
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    response = WorkspaceCreate.as_view()(request)

    assert response.status_code == 302

    workspace = Workspace.objects.first()
    assert response.url == reverse("workspace-detail", kwargs={"name": workspace.name})
    assert workspace.created_by == user


@pytest.mark.django_db
@responses.activate
def test_workspacecreate_unauthorized(rf, user):
    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
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

    response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 200

    assert response.context_data["workspace"] == workspace


@pytest.mark.django_db
def test_workspacedetail_project_yaml_errors(rf, mocker, user):
    workspace = WorkspaceFactory()

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project",
        autospec=True,
        side_effect=Exception("test error"),
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 200

    assert response.context_data["actions"] == []
    assert response.context_data["actions_error"] == "test error"


@pytest.mark.django_db
def test_workspacedetail_get_success(rf, mocker, user):
    workspace = WorkspaceFactory()

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": [], "status": "-"},
        {"name": "run_all", "needs": ["twiddle"], "status": "-"},
    ]
    assert response.context_data["workspace"] == workspace


@pytest.mark.django_db
def test_workspacedetail_post_archived_workspace(rf, mocker):
    workspace = WorkspaceFactory(is_archived=True)

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_actions", autospec=True, return_value=[]
    )

    request = rf.post(MEANINGLESS_URL)
    request.session = "session"
    request._messages = FallbackStorage(request)
    request.user = UserFactory()

    response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()


@pytest.mark.django_db
def test_workspacedetail_post_success(rf, mocker, monkeypatch, user):
    monkeypatch.setenv("BACKENDS", "tpp")

    workspace = WorkspaceFactory()

    tpp = Backend.objects.get(name="tpp")
    BackendMembershipFactory(backend=tpp, user=user)

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_branch_sha",
        autospec=True,
        return_value="abc123",
    )

    data = {
        "backend": "tpp",
        "requested_actions": ["twiddle"],
        "callback_url": "test",
    }
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

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
def test_workspacedetail_post_with_invalid_backend(rf, mocker, monkeypatch, user):
    monkeypatch.setenv("BACKENDS", "tpp,emis")

    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=Backend.objects.get(name="tpp"), user=user)

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_branch_sha",
        autospec=True,
        return_value="abc123",
    )

    data = {
        "backend": "emis",
        "requested_actions": ["twiddle"],
        "callback_url": "test",
    }
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    response = GlobalWorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 200
    assert response.context_data["form"].errors["backend"] == [
        "Select a valid choice. emis is not one of the available choices."
    ]


@pytest.mark.django_db
def test_workspacedetail_post_with_notifications_default(rf, mocker, monkeypatch, user):
    monkeypatch.setenv("BACKENDS", "tpp")

    workspace = WorkspaceFactory(should_notify=True)

    BackendMembershipFactory(backend=Backend.objects.get(name="tpp"), user=user)

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_branch_sha",
        autospec=True,
        return_value="abc123",
    )

    data = {
        "backend": "tpp",
        "requested_actions": ["twiddle"],
        "callback_url": "test",
        "will_notify": "True",
    }
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

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
def test_workspacedetail_post_with_notifications_override(
    rf, mocker, monkeypatch, user
):
    monkeypatch.setenv("BACKENDS", "tpp")

    workspace = WorkspaceFactory(should_notify=True)

    BackendMembershipFactory(backend=Backend.objects.get(name="tpp"), user=user)

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_branch_sha",
        autospec=True,
        return_value="abc123",
    )

    data = {
        "backend": "tpp",
        "requested_actions": ["twiddle"],
        "callback_url": "test",
        "will_notify": "False",
    }
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

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
def test_workspacelog_search_by_action(rf, mocker):
    workspace = WorkspaceFactory()
    user = UserFactory()

    job_request1 = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request1, action="run")

    job_request2 = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request2, action="leap")

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )

    request = rf.get("/?q=run")
    request.user = user

    response = WorkspaceLog.as_view()(request, name=workspace.name)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request1


@pytest.mark.django_db
def test_workspacelog_search_by_id(rf, mocker):
    workspace = WorkspaceFactory()
    user = UserFactory()

    JobFactory(job_request=JobRequestFactory())

    job_request2 = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request2, id=99)

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )

    request = rf.get("/?q=99")
    request.user = user

    response = WorkspaceLog.as_view()(request, name=workspace.name)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request2


@pytest.mark.django_db
def test_workspacelog_success(rf, mocker):
    workspace = WorkspaceFactory()
    user = UserFactory()
    job_request = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request)

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

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
def test_workspacelog_with_authenticated_user(rf, mocker):
    """
    Check WorkspaceLog renders the Add Job button for authenticated Users
    """
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request)

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

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
def test_workspacenotificationstoggle_success(rf, user):
    workspace = WorkspaceFactory(should_notify=True)

    request = rf.post(MEANINGLESS_URL, {"should_notify": ""})
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = WorkspaceNotificationsToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    workspace.refresh_from_db()

    assert not workspace.should_notify


@pytest.mark.django_db
@responses.activate
def test_workspacenotificationstoggle_unauthorized(rf, user):
    workspace = WorkspaceFactory()

    request = rf.post(MEANINGLESS_URL, {"should_notify": ""})
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = WorkspaceNotificationsToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
@responses.activate
def test_workspacenotificationstoggle_unknown_workspace(rf, user):
    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    with pytest.raises(Http404):
        WorkspaceNotificationsToggle.as_view()(request, name="test")


@pytest.mark.django_db
@responses.activate
def test_workspacerelease_unauthorized(rf, user):
    request = rf.get(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = WorkspaceReleaseView.as_view()(request)
    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"
