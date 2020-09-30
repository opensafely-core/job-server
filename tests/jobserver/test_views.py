import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Job, Workspace
from jobserver.views import JobCreate, JobList, Login, WorkspaceCreate, WorkspaceList

from ..factories import JobFactory, UserFactory, WorkspaceFactory


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
    JobFactory()
    JobFactory(completed_at=timezone.now())

    request = rf.get("/?status=completed")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_joblist_filter_by_status_and_workspace(rf):
    workspace = WorkspaceFactory()
    JobFactory(workspace=workspace, started_at=timezone.now())
    JobFactory(workspace=workspace)

    request = rf.get(f"/?status=in-progress&workspace={workspace.pk}")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_joblist_filter_by_workspace(rf):
    workspace = WorkspaceFactory()
    JobFactory(workspace=workspace)
    JobFactory()

    request = rf.get(f"/?workspace={workspace.pk}")
    response = JobList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


def test_login(rf):
    request = rf.get("/")
    response = Login.as_view()(request)

    assert "form_helper" in response.context_data


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
