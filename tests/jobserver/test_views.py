import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Job, Workspace
from jobserver.views import JobCreate, JobList, WorkspaceCreate, WorkspaceList

from ..factories import JobFactory, JobRequestFactory, UserFactory, WorkspaceFactory


@pytest.mark.django_db
def test_jobcreate_redirects_to_new_job(rf):
    data = {
        "workspace": WorkspaceFactory().pk,
        "force_run": "test",
        "force_run_dependencies": "test",
        "action_id": "test",
        "backend": "test",
        "callback_url": "test",
    }

    request = rf.post("/", data)
    request.user = UserFactory()
    response = JobCreate.as_view()(request)

    assert response.status_code == 302

    pk = Job.objects.first().pk
    assert response.url == reverse("job-detail", kwargs={"pk": pk})


@pytest.mark.django_db
def test_joblist_filters_exist(rf):
    request = rf.get("/")
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

    request = rf.get(f"/?status=in-progress&workspace={workspace2.pk}")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_joblist_filter_by_workspace(rf):
    workspace = WorkspaceFactory()
    JobRequestFactory(workspace=workspace)
    JobRequestFactory()

    request = rf.get(f"/?workspace={workspace.pk}")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_joblist_search_by_action(rf):
    request1 = JobRequestFactory()
    JobFactory(request=request1, action_id="run")

    request2 = JobRequestFactory()
    JobFactory(request=request2, action_id="leap")

    request = rf.get("/?q=run")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == request1


@pytest.mark.django_db
def test_joblist_search_by_id(rf):
    JobFactory(request=JobRequestFactory())

    request2 = JobRequestFactory()
    JobFactory(request=request2, id=99)

    request = rf.get("/?q=99")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == request2


@pytest.mark.django_db
def test_workspacecreate_redirects_to_new_workspace(rf):
    data = {
        "name": "Test",
        "repo": "test",
        "branch": "test",
        "owner": "test",
        "db": "dummy",
    }

    request = rf.post("/", data)
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
    request = rf.get("/")
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
    request = rf.get("/")
    request.user = AnonymousUser()
    response = WorkspaceList.as_view()(request)

    assert response.status_code == 200
