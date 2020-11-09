from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from jobserver.models import JobRequest, Workspace
from jobserver.views import (
    Dashboard,
    JobRequestCreate,
    JobRequestList,
    JobRequestZombify,
    JobZombify,
    WorkspaceCreate,
    WorkspaceList,
    WorkspaceSelectOrCreate,
)

from ..factories import (
    JobFactory,
    JobRequestFactory,
    UserFactory,
    UserSocialAuthFactory,
    WorkspaceFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_dashboard_other_users_jobs(rf):
    job_request = JobRequestFactory(created_by=UserFactory())
    JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = Dashboard.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 0


@pytest.mark.django_db
def test_dashboard_search_by_action(rf):
    user = UserFactory()

    job_request1 = JobRequestFactory(created_by=user)
    JobFactory(job_request=job_request1, action_id="run")

    job_request2 = JobRequestFactory()
    JobFactory(job_request=job_request2, action_id="leap")

    # Build a RequestFactory instance
    request = rf.get("/?q=run")
    request.user = user
    response = Dashboard.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request1


@pytest.mark.django_db
def test_dashboard_search_by_id(rf):
    user = UserFactory()

    JobFactory(job_request=JobRequestFactory())

    job_request2 = JobRequestFactory(created_by=user)
    JobFactory(job_request=job_request2, id=99)

    # Build a RequestFactory instance
    request = rf.get("/?q=99")
    request.user = user
    response = Dashboard.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request2


@pytest.mark.django_db
def test_dashboard_success(rf):
    user = UserFactory()
    job_request = JobRequestFactory(created_by=user)
    JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = user
    response = Dashboard.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_dashboard_unauthenticed_redirect(rf):
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()
    response = Dashboard.as_view()(request)

    assert response.status_code == 302
    assert response.url == reverse("job-list")


@pytest.mark.django_db
def test_dashboard_filter_by_workspace(rf):
    user = UserFactory()

    workspace = WorkspaceFactory()
    JobRequestFactory(created_by=user, workspace=workspace)
    JobRequestFactory(created_by=user)

    # Build a RequestFactory instance
    request = rf.get(f"/?workspace={workspace.pk}")
    request.user = user
    response = Dashboard.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_jobdetail_with_newer_job(rf):
    job_request = JobRequestFactory(workspace=WorkspaceFactory())
    job = JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobRequestList.as_view()(request, pk=job.pk)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_older_job(rf):
    job = JobFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobRequestList.as_view()(request, pk=job.pk)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobzombify_not_superuser(client):
    job = JobFactory(started=True, completed_at=None, status_code=None)

    client.force_login(UserFactory(is_superuser=False))
    response = client.post(f"/jobs/{job.pk}/zombify/", follow=True)

    assert response.status_code == 200

    # did we redirect to the correct JobDetail page?
    url = reverse("job-detail", kwargs={"pk": job.pk})
    assert response.redirect_chain == [(url, 302)]

    # has the Job been left untouched?
    job.refresh_from_db()
    assert job.status_code is None
    assert job.status_message == ""

    # did we produce a message?
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Only admins can zombify Jobs."


@pytest.mark.django_db
def test_jobzombify_success(rf):
    job = JobFactory(started=True, completed_at=None, status_code=None)

    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)

    response = JobZombify.as_view()(request, pk=job.pk)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"pk": job.pk})

    job.refresh_from_db()

    assert job.status_code == 10
    assert job.status_message == "Job manually zombified"


@pytest.mark.django_db
def test_jobzombify_unknown_job(rf):
    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)

    with pytest.raises(Http404):
        JobZombify.as_view()(request, pk="99")


@pytest.mark.django_db
def test_jobrequestcreate_get_success(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = user

    dummy_project = [{"name": "twiddle", "needs": []}]
    with patch("jobserver.views.get_actions", new=lambda r, b: dummy_project):
        response = JobRequestCreate.as_view()(request, pk=workspace.pk)

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": [], "status": "-"}
    ]

    assert response.context_data["branch"] == workspace.branch


@pytest.mark.django_db
def test_jobrequestcreate_post_success(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    data = {
        "requested_actions": ["twiddle"],
        "callback_url": "test",
    }

    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    dummy_project = [{"name": "twiddle", "needs": []}]
    with patch("jobserver.views.get_actions", new=lambda r, b: dummy_project), patch(
        "jobserver.views.get_branch_sha", new=lambda r, b: "abc123"
    ):
        response = JobRequestCreate.as_view()(request, pk=workspace.pk)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == reverse("job-list")

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend == "tpp"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert job_request.jobs.count() == 1


@pytest.mark.django_db
def test_jobrequestcreate_unknown_workspace_redirects_to_select_workspace_form(client):
    client.force_login(UserFactory())

    with patch("jobserver.views.get_repos_with_branches", new=lambda *args: []):
        response = client.post("/jobs/new/0/", follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("job-select-workspace"), 302)]

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Unknown Workspace, please pick a valid one"


@pytest.mark.django_db
def test_jobrequestlist_filters_exist(rf):
    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobRequestList.as_view()(request)

    assert "statuses" in response.context_data
    assert "workspaces" in response.context_data


@pytest.mark.django_db
def test_jobrequestlist_filter_by_status(rf):
    job_request1 = JobRequestFactory()
    JobFactory(job_request=job_request1)

    job_request2 = JobRequestFactory()
    JobFactory.create_batch(
        2,
        job_request=job_request2,
        started=True,
        completed_at=timezone.now(),
        status_code=0,
    )

    # Build a RequestFactory instance
    request = rf.get("/?status=succeeded")
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_jobrequestlist_filter_by_status_and_workspace(rf):
    workspace1 = WorkspaceFactory()
    workspace2 = WorkspaceFactory()

    # running
    job_request1 = JobRequestFactory(workspace=workspace1)
    JobFactory(
        job_request=job_request1, started=True, started_at=timezone.now(), status_code=0
    )
    JobFactory(job_request=job_request1, started=True)

    # failed
    job_request2 = JobRequestFactory(workspace=workspace1)
    JobFactory(
        job_request=job_request2,
        started=True,
        completed_at=timezone.now(),
        status_code=0,
    )
    JobFactory(job_request=job_request2, started=True, status_code=3)

    # running
    job_request3 = JobRequestFactory(workspace=workspace2)
    JobFactory.create_batch(
        2,
        job_request=job_request3,
        started=True,
        completed_at=timezone.now(),
        status_code=0,
    )
    JobFactory.create_batch(2, job_request=job_request3, started=True)

    # succeeded
    job_request4 = JobRequestFactory(workspace=workspace2)
    JobFactory.create_batch(
        3,
        job_request=job_request4,
        started=True,
        completed_at=timezone.now(),
        status_code=0,
    )

    # Build a RequestFactory instance
    request = rf.get(f"/?status=running&workspace={workspace2.pk}")
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_jobrequestlist_filter_by_username(rf):
    user = UserFactory()
    JobRequestFactory(created_by=user)
    JobRequestFactory(created_by=UserFactory())

    # Build a RequestFactory instance
    request = rf.get(f"/?username={user.username}")
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_jobrequestlist_filter_by_workspace(rf):
    workspace = WorkspaceFactory()
    JobRequestFactory(workspace=workspace)
    JobRequestFactory()

    # Build a RequestFactory instance
    request = rf.get(f"/?workspace={workspace.pk}")
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_jobrequestlist_search_by_action(rf):
    job_request1 = JobRequestFactory()
    JobFactory(job_request=job_request1, action_id="run")

    job_request2 = JobRequestFactory()
    JobFactory(job_request=job_request2, action_id="leap")

    # Build a RequestFactory instance
    request = rf.get("/?q=run")
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request1


@pytest.mark.django_db
def test_jobrequestlist_search_by_id(rf):
    JobFactory(job_request=JobRequestFactory())

    job_request2 = JobRequestFactory()
    JobFactory(job_request=job_request2, id=99)

    # Build a RequestFactory instance
    request = rf.get("/?q=99")
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request2


@pytest.mark.django_db
def test_jobrequestlist_success(rf):
    user = UserSocialAuthFactory().user

    job_request = JobRequestFactory(created_by=user)
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request

    assert response.context_data["users"] == {user.username: user.name}
    assert len(response.context_data["workspaces"]) == 1


@pytest.mark.django_db
def test_jobrequestzombify_not_superuser(client):
    job_request = JobRequestFactory()
    JobFactory.create_batch(
        5,
        job_request=job_request,
        started=True,
        completed_at=None,
        status_code=None,
    )

    client.force_login(UserFactory(is_superuser=False))
    response = client.post(f"/job-requests/{job_request.pk}/zombify/", follow=True)

    assert response.status_code == 200

    # did we redirect to the correct JobDetail page?
    url = reverse("job-request-detail", kwargs={"pk": job_request.pk})
    assert response.redirect_chain == [(url, 302)]

    # has the Job been left untouched?
    job_request.refresh_from_db()
    for job in job_request.jobs.all():
        assert job.status_code is None
        assert job.status_message == ""

    # did we produce a message?
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Only admins can zombify Jobs."


@pytest.mark.django_db
def test_jobrequestzombify_success(rf):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, started=False)
    JobFactory(
        job_request=job_request, started=True, completed_at=None, status_code=None
    )

    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)

    response = JobRequestZombify.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == reverse("job-request-detail", kwargs={"pk": job_request.pk})

    jobs = job_request.jobs.all()

    assert all(j.status_code == 10 for j in jobs)
    assert all(j.status_message == "Job manually zombified" for j in jobs)


@pytest.mark.django_db
def test_jobrequestzombify_unknown_jobrequest(rf):
    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)

    with pytest.raises(Http404):
        JobRequestZombify.as_view()(request, pk="99")


@pytest.mark.django_db
def test_workspacecreate_redirects_to_new_workspace(rf):
    user = UserFactory()
    data = {
        "name": "Test",
        "repo": "test",
        "branch": "test",
        "db": "dummy",
    }

    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    repos = [{"name": "Test", "url": "test", "branches": ["test"]}]
    with patch("jobserver.views.get_repos_with_branches", new=lambda *args: repos):
        response = WorkspaceCreate.as_view()(request)

    assert response.status_code == 302

    workspace = Workspace.objects.first()

    assert response.url == reverse("workspace-detail", kwargs={"pk": workspace.pk})

    assert workspace.created_by == user


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
        "db": "dummy",
    }
    # Build a RequestFactory instance
    request = rf.post(MEANINGLESS_URL, data)
    request.user = UserFactory()

    repos = [{"name": "Test", "url": "test", "branches": ["test"]}]
    with patch("jobserver.views.get_repos_with_branches", new=lambda *args: repos):
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
    with patch("jobserver.views.get_repos_with_branches", new=lambda *args: []):
        response = WorkspaceSelectOrCreate.as_view()(request)
    assert response.status_code == 200
    assert len(response.context_data["workspace_list"]) == 2
