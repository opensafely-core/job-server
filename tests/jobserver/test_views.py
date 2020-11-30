from datetime import timedelta
from unittest.mock import patch

import pytest
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from jobserver.models import JobRequest, Workspace
from jobserver.views import (
    Index,
    JobDetail,
    JobRequestList,
    JobRequestZombify,
    JobZombify,
    Status,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceLog,
)

from ..factories import (
    JobFactory,
    JobRequestFactory,
    StatsFactory,
    UserFactory,
    UserSocialAuthFactory,
    WorkspaceFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_index_success(rf):
    JobRequestFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = Index.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["job_requests"]) == 1
    assert len(response.context_data["workspaces"]) == 1


@pytest.mark.django_db
def test_jobdetail_with_identifier(rf):
    job = JobFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobDetail.as_view()(request, identifier=job.pk)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_pk(rf):
    job = JobFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobDetail.as_view()(request, identifier=job.pk)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_post_jobrequest_job(rf):
    job = JobFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobDetail.as_view()(request, identifier=job.pk)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_pre_jobrequest_job(rf):
    job_request = JobRequestFactory(workspace=WorkspaceFactory())
    job = JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobDetail.as_view()(request, identifier=job.pk)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_unknown_job(rf):
    request = rf.get(MEANINGLESS_URL)

    with pytest.raises(Http404):
        JobDetail.as_view()(request, identifier="test")


@pytest.mark.django_db
def test_jobzombify_not_superuser(client):
    job = JobFactory(started=True, completed_at=None, status_code=None)

    client.force_login(UserFactory(is_superuser=False))
    response = client.post(f"/jobs/{job.identifier}/zombify/", follow=True)

    assert response.status_code == 200

    # did we redirect to the correct JobDetail page?
    url = reverse("job-detail", kwargs={"identifier": job.identifier})
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

    response = JobZombify.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job.refresh_from_db()

    assert job.status_code == 10
    assert job.status_message == "Job manually zombified"


@pytest.mark.django_db
def test_jobzombify_unknown_job(rf):
    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)

    with pytest.raises(Http404):
        JobZombify.as_view()(request, identifier="")


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
    JobFactory(job_request=job_request1, action="run")

    job_request2 = JobRequestFactory()
    JobFactory(job_request=job_request2, action="leap")

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
def test_status_healthy(rf):
    JobFactory.create_batch(3, started=True, completed_at=None)

    last_seen = timezone.now() - timedelta(minutes=1)
    StatsFactory(api_last_seen=last_seen)

    request = rf.get(MEANINGLESS_URL)
    response = Status.as_view()(request)

    tpp = response.context_data["backends"][0]

    assert tpp["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert tpp["queue"]["acked"] == 3
    assert tpp["queue"]["unacked"] == 0
    assert not tpp["show_warning"]


@pytest.mark.django_db
def test_status_no_last_seen(rf):
    JobFactory(started=False)

    request = rf.get(MEANINGLESS_URL)
    response = Status.as_view()(request)

    tpp = response.context_data["backends"][0]

    assert tpp["last_seen"] == "never"
    assert not tpp["show_warning"]


@pytest.mark.django_db
def test_status_unacked_jobs_but_recent_api_contact(rf):
    JobFactory(started=False)

    last_seen = timezone.now() - timedelta(minutes=1)
    StatsFactory(api_last_seen=last_seen)

    request = rf.get(MEANINGLESS_URL)
    response = Status.as_view()(request)

    tpp = response.context_data["backends"][0]

    assert tpp["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert not tpp["show_warning"]


@pytest.mark.django_db
def test_status_unhealthy(rf):
    JobFactory(started=False, completed_at=None)
    JobFactory(started=True, completed_at=None)
    JobFactory(started=True, completed_at=None)

    last_seen = timezone.now() - timedelta(minutes=10)
    StatsFactory(api_last_seen=last_seen)

    request = rf.get(MEANINGLESS_URL)
    response = Status.as_view()(request)

    tpp = response.context_data["backends"][0]

    assert tpp["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert tpp["queue"]["acked"] == 2
    assert tpp["queue"]["unacked"] == 1
    assert tpp["show_warning"]


@pytest.mark.django_db
def test_workspacecreate_get_success(rf):
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    with patch("jobserver.views.get_repos_with_branches", new=lambda *args: []):
        response = WorkspaceCreate.as_view()(request)

    assert response.status_code == 200
    assert response.context_data["repos_with_branches"] == []


@pytest.mark.django_db
def test_workspacecreate_post_success(rf):
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
    assert response.url == reverse("workspace-detail", kwargs={"name": workspace.name})
    assert workspace.created_by == user


@pytest.mark.django_db
def test_workspacedetail_get_success(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = user

    dummy_project = [
        {"name": "twiddle", "needs": []},
        {"name": "run_all", "needs": ["twiddle"]},
    ]
    with patch("jobserver.views.get_actions", new=lambda r, b: dummy_project):
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "run_all", "needs": ["twiddle"], "status": "-"},
        {"name": "twiddle", "needs": [], "status": "-"},
    ]

    assert response.context_data["branch"] == workspace.branch


@pytest.mark.django_db
def test_workspacedetail_without_run_all(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = user

    dummy_project = [{"name": "twiddle", "needs": []}]
    with patch("jobserver.views.get_actions", new=lambda r, b: dummy_project):
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": [], "status": "-"},
        {"name": "run_all", "needs": ["twiddle"], "status": "-"},
    ]

    assert response.context_data["branch"] == workspace.branch


@pytest.mark.django_db
def test_workspacedetail_post_success(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

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
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

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
def test_workspacedetail_unknown_workspace(rf):
    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = WorkspaceDetail.as_view()(request, name="test")

    assert response.status_code == 302
    assert response.url == "/"


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
