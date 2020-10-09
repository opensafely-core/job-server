import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils import timezone

from jobserver.models import JobRequest, Workspace
from jobserver.views import (
    JobList,
    JobRequestCreate,
    WorkspaceCreate,
    WorkspaceList,
    WorkspaceSelectOrCreate,
)

from ..factories import JobFactory, JobRequestFactory, UserFactory, WorkspaceFactory


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_joblist_filters_exist(rf):
    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobList.as_view()(request)

    assert "statuses" in response.context_data
    assert "workspaces" in response.context_data


@pytest.mark.django_db
def test_joblist_filter_by_status(rf):
    request1 = JobRequestFactory()
    JobFactory(request=request1)

    request2 = JobRequestFactory()
    JobFactory(request=request2, completed_at=timezone.now())
    JobFactory(request=request2, completed_at=timezone.now())

    # Build a RequestFactory instance
    request = rf.get("/?status=completed")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_joblist_filter_by_status_and_workspace(rf):
    workspace1 = WorkspaceFactory()
    workspace2 = WorkspaceFactory()

    # in progress
    request1 = JobRequestFactory(workspace=workspace1)
    JobFactory(request=request1, started_at=timezone.now())
    JobFactory(request=request1)

    # failed
    request2 = JobRequestFactory(workspace=workspace1)
    JobFactory(request=request2, completed_at=timezone.now())
    JobFactory(request=request2, status_code=3)

    # in progress
    request3 = JobRequestFactory(workspace=workspace2)
    JobFactory(request=request3, completed_at=timezone.now())
    JobFactory(request=request3, completed_at=timezone.now())
    JobFactory(request=request3, started_at=timezone.now())
    JobFactory(request=request3)

    # complete
    request4 = JobRequestFactory(workspace=workspace2)
    JobFactory(request=request4, completed_at=timezone.now())
    JobFactory(request=request4, completed_at=timezone.now())
    JobFactory(request=request4, completed_at=timezone.now())

    # Build a RequestFactory instance
    request = rf.get(f"/?status=in-progress&workspace={workspace2.pk}")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_joblist_filter_by_workspace(rf):
    workspace = WorkspaceFactory()
    JobRequestFactory(workspace=workspace)
    JobRequestFactory()

    # Build a RequestFactory instance
    request = rf.get(f"/?workspace={workspace.pk}")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_joblist_search_by_action(rf):
    request1 = JobRequestFactory()
    JobFactory(request=request1, action_id="run")

    request2 = JobRequestFactory()
    JobFactory(request=request2, action_id="leap")

    # Build a RequestFactory instance
    request = rf.get("/?q=run")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == request1


@pytest.mark.django_db
def test_joblist_search_by_id(rf):
    JobFactory(request=JobRequestFactory())

    request2 = JobRequestFactory()
    JobFactory(request=request2, id=99)

    # Build a RequestFactory instance
    request = rf.get("/?q=99")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == request2


@pytest.mark.django_db
def test_jobrequestcreate_success_with_one_backend(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    data = {
        "branch": "test",
        "requested_action": "twiddle",
        "backends": "tpp",
        "callback_url": "test",
    }

    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user
    response = JobRequestCreate.as_view()(request, pk=workspace.pk)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == reverse("job-list")

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend == "tpp"
    assert job_request.requested_action == "twiddle"
    assert not job_request.jobs.exists()


@pytest.mark.django_db
def test_jobrequestcreate_success_with_all_backends(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    data = {
        "branch": "test",
        "requested_action": "twiddle",
        "backends": "all",
        "callback_url": "test",
    }

    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user
    response = JobRequestCreate.as_view()(request, pk=workspace.pk)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == reverse("job-list")

    job_requests = JobRequest.objects.all()

    assert len(job_requests) == 2

    job_request1 = job_requests[0]
    assert job_request1.created_by == user
    assert job_request1.workspace == workspace
    assert job_request1.backend == "emis"
    assert job_request1.requested_action == "twiddle"
    assert not job_request1.jobs.exists()

    job_request2 = job_requests[1]
    assert job_request2.created_by == user
    assert job_request2.workspace == workspace
    assert job_request2.backend == "tpp"
    assert job_request2.requested_action == "twiddle"
    assert not job_request2.jobs.exists()


@pytest.mark.django_db
def test_jobrequestcreate_unknown_workspace_redirects_to_select_workspace_form(client):
    client.force_login(UserFactory())
    response = client.post("/jobs/new/0/", follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("job-select-workspace"), 302)]

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Unknown Workspace, please pick a valid one"


@pytest.mark.django_db
def test_workspacecreate_redirects_to_new_workspace(rf):
    data = {
        "name": "Test",
        "repo": "test",
        "branch": "test",
        "owner": "test",
        "db": "dummy",
    }

    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = UserFactory()
    response = WorkspaceCreate.as_view()(request)

    assert response.status_code == 302

    pk = Workspace.objects.first().pk
    assert response.url == reverse("workspace-detail", kwargs={"pk": pk})


@pytest.mark.django_db
def test_workspacelist_redirects_user_without_workspaces(rf):
    """
    Check authenticated users are redirected when there are no workspaces

    Authenticated users can add workspaces so we want them to be redirected to
    the workspace create page when there aren't any to show in the list page.
    """
    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = WorkspaceList.as_view()(request)

    assert response.status_code == 302
    assert response.url == reverse("workspace-create")


@pytest.mark.django_db
def test_workspacelist_does_not_redirect_anon_users(rf):
    """
    Check anonymous users see an empty workspace list page

    Anonymous users can't add workspaces so redirecting them to the workspace
    create page would be a poor experience.  Instead show them the empty
    workspace list page.
    """
    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()
    response = WorkspaceList.as_view()(request)

    assert response.status_code == 200


@pytest.mark.django_db
def test_workspaceselectorcreate_redirects_to_new_workspace(rf):
    data = {
        "name": "Test",
        "repo": "test",
        "branch": "test",
        "owner": "test",
        "db": "dummy",
    }
    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = UserFactory()
    response = WorkspaceSelectOrCreate.as_view()(request)

    assert response.status_code == 302

    pk = Workspace.objects.first().pk
    assert response.url == reverse("job-create", kwargs={"pk": pk})


@pytest.mark.django_db
def test_workspaceselectorcreate_success(rf):
    WorkspaceFactory()
    WorkspaceFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = WorkspaceSelectOrCreate.as_view()(request)
    assert response.status_code == 200
    assert len(response.context_data["workspace_list"]) == 2
