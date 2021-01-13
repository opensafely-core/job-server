from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from first import first

from jobserver.models import Backend, JobRequest, Workspace
from jobserver.views import (
    BackendDetail,
    BackendList,
    BackendRotateToken,
    Index,
    JobDetail,
    JobRequestList,
    JobRequestZombify,
    JobZombify,
    Settings,
    Status,
    WorkspaceArchive,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceLog,
    WorkspaceNotificationsToggle,
    WorkspaceUnarchive,
    superuser_required,
)

from ..factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    StatsFactory,
    UserFactory,
    UserSocialAuthFactory,
    WorkspaceFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_superuserrequired_with_superuser(rf):
    request = rf.get(MEANINGLESS_URL)
    request.session = "session"
    request._messages = FallbackStorage(request)
    request.user = UserFactory(is_superuser=True)

    def dispatch(request):
        return request

    returned_request = superuser_required(dispatch)(request)

    # check the request is passed through the decorator
    assert returned_request == request


@pytest.mark.django_db
def test_superuserrequired_without_superuser(rf):
    request = rf.get(MEANINGLESS_URL)
    request.session = "session"
    request._messages = FallbackStorage(request)
    request.user = UserFactory(is_superuser=False)

    response = superuser_required(None)(request)

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_backenddetail_success(rf):
    backend = BackendFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)
    response = BackendDetail.as_view()(request, pk=backend.pk)

    assert response.status_code == 200
    assert response.context_data["backend"] == backend


@pytest.mark.django_db
def test_backendlist_success(rf):
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)
    response = BackendList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 3


@pytest.mark.django_db
def test_backendrotatetoken_success(rf):
    backend = BackendFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)
    response = BackendRotateToken.as_view()(request, pk=backend.pk)

    assert response.status_code == 302
    assert response.url == reverse("backend-detail", kwargs={"pk": backend.pk})


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
def test_jobdetail_with_post_jobrequest_job(rf):
    job = JobFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_pre_jobrequest_job(rf):
    job_request = JobRequestFactory(workspace=WorkspaceFactory())
    job = JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_unknown_job(rf):
    request = rf.get(MEANINGLESS_URL)

    with pytest.raises(Http404):
        JobDetail.as_view()(request, identifier="test")


@pytest.mark.django_db
def test_jobzombify_not_superuser(client):
    job = JobFactory(completed_at=None)

    client.force_login(UserFactory(is_superuser=False))
    response = client.post(f"/jobs/{job.identifier}/zombify/", follow=True)

    assert response.status_code == 200

    # did we redirect to the correct JobDetail page?
    url = reverse("job-detail", kwargs={"identifier": job.identifier})
    assert response.redirect_chain == [(url, 302)]

    # has the Job been left untouched?
    job.refresh_from_db()
    assert job.status == ""
    assert job.status_message == ""

    # did we produce a message?
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Only admins can zombify Jobs."


@pytest.mark.django_db
def test_jobzombify_success(rf):
    job = JobFactory(completed_at=None)

    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)

    response = JobZombify.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job.refresh_from_db()

    assert job.status == "failed"
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
    JobFactory(job_request=JobRequestFactory(), status="failed")

    JobFactory(job_request=JobRequestFactory(), status="succeeded")

    # Build a RequestFactory instance
    request = rf.get("/?status=succeeded")
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["page_obj"]) == 1


@pytest.mark.django_db
def test_jobrequestlist_filter_by_status_and_workspace(rf):
    workspace1 = WorkspaceFactory()
    workspace2 = WorkspaceFactory()

    # running
    job_request1 = JobRequestFactory(workspace=workspace1)
    JobFactory(job_request=job_request1, status="running")
    JobFactory(job_request=job_request1, status="pending")

    # failed
    job_request2 = JobRequestFactory(workspace=workspace1)
    JobFactory(job_request=job_request2, status="succeeded")
    JobFactory(job_request=job_request2, status="failed")

    # running
    job_request3 = JobRequestFactory(workspace=workspace2)
    JobFactory.create_batch(2, job_request=job_request3, status="succeeded")
    JobFactory.create_batch(2, job_request=job_request3, status="pending")

    # succeeded
    job_request4 = JobRequestFactory(workspace=workspace2)
    JobFactory.create_batch(3, job_request=job_request4, status="succeeded")

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
        completed_at=None,
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
        assert job.status == ""
        assert job.status_message == ""

    # did we produce a message?
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Only admins can zombify Jobs."


@pytest.mark.django_db
def test_jobrequestzombify_success(rf):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request, completed_at=None)

    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)

    response = JobRequestZombify.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == reverse("job-request-detail", kwargs={"pk": job_request.pk})

    jobs = job_request.jobs.all()

    assert all(j.status == "failed" for j in jobs)
    assert all(j.status_message == "Job manually zombified" for j in jobs)


@pytest.mark.django_db
def test_jobrequestzombify_unknown_jobrequest(rf):
    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=True)

    with pytest.raises(Http404):
        JobRequestZombify.as_view()(request, pk="99")


@pytest.mark.django_db
def test_settings_get(rf):
    UserFactory()
    user2 = UserFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = user2
    response = Settings.as_view()(request)

    assert response.status_code == 200

    # check the view was constructed with the request user
    assert response.context_data["object"] == user2


@pytest.mark.django_db
def test_settings_post(rf):
    UserFactory()
    user2 = UserFactory(notifications_email="original@example.com")

    data = {"notifications_email": "changed@example.com"}

    request = rf.post(MEANINGLESS_URL, data)
    request.user = user2
    response = Settings.as_view()(request)

    assert response.status_code == 302
    assert response.url == reverse("settings")

    user2.refresh_from_db()

    assert user2.notifications_email == "changed@example.com"


@pytest.mark.django_db
def test_status_healthy(rf):
    tpp = Backend.objects.get(name="tpp")

    # acked, because JobFactory will implicitly create JobRequests
    JobFactory.create_batch(3, job_request__backend=tpp)

    last_seen = timezone.now() - timedelta(minutes=1)
    StatsFactory(backend=tpp, api_last_seen=last_seen)

    request = rf.get(MEANINGLESS_URL)
    response = Status.as_view()(request)

    tpp_output = first(
        response.context_data["backends"], key=lambda b: b["name"] == "TPP"
    )

    assert tpp_output["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert tpp_output["queue"]["acked"] == 3
    assert tpp_output["queue"]["unacked"] == 0
    assert not tpp_output["show_warning"]


@pytest.mark.django_db
def test_status_no_last_seen(rf):
    request = rf.get(MEANINGLESS_URL)
    response = Status.as_view()(request)

    tpp_output = first(
        response.context_data["backends"], key=lambda b: b["name"] == "TPP"
    )

    assert tpp_output["last_seen"] == "never"
    assert not tpp_output["show_warning"]


@pytest.mark.django_db
def test_status_unacked_jobs_but_recent_api_contact(rf):
    tpp = Backend.objects.get(name="tpp")

    last_seen = timezone.now() - timedelta(minutes=1)
    StatsFactory(backend=tpp, api_last_seen=last_seen)

    request = rf.get(MEANINGLESS_URL)
    response = Status.as_view()(request)

    tpp_output = first(
        response.context_data["backends"], key=lambda b: b["name"] == "TPP"
    )

    assert tpp_output["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert not tpp_output["show_warning"]


@pytest.mark.django_db
def test_status_unhealthy(rf):
    # backends are created by migrations so we can depend on them
    tpp = Backend.objects.get(name="tpp")

    # acked, because JobFactory will implicitly create JobRequests
    JobFactory.create_batch(2, job_request__backend=tpp)

    # unacked, because it has no Jobs
    JobRequestFactory(backend=tpp)

    last_seen = timezone.now() - timedelta(minutes=10)
    StatsFactory(backend=tpp, api_last_seen=last_seen, url="foo")

    request = rf.get(MEANINGLESS_URL)
    response = Status.as_view()(request)

    tpp_output = first(
        response.context_data["backends"], key=lambda b: b["name"] == "TPP"
    )

    assert tpp_output["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert tpp_output["queue"]["acked"] == 2
    assert tpp_output["queue"]["unacked"] == 1
    assert tpp_output["show_warning"]


@pytest.mark.django_db
def test_workspacearchive_already_archived(rf):
    workspace = WorkspaceFactory(is_archived=True)

    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory()

    response = WorkspaceArchive.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == "/"

    workspace.refresh_from_db()
    assert workspace.is_archived


@pytest.mark.django_db
def test_workspacearchive_success(rf):
    workspace = WorkspaceFactory(is_archived=False)

    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory()

    response = WorkspaceArchive.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == "/"

    workspace.refresh_from_db()
    assert workspace.is_archived


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
        "db": "slice",
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
def test_workspacedetail_logged_out(rf):
    workspace = WorkspaceFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()

    with patch("jobserver.views.get_actions") as mocked_get_actions:
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

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

    with patch("jobserver.views.get_actions", side_effect=Exception("test error")):
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

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

    dummy_project = [{"name": "twiddle", "needs": [], "status": "-"}]
    with patch("jobserver.views.get_actions", new=lambda *args: dummy_project):
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": [], "status": "-"},
    ]
    assert response.context_data["branch"] == workspace.branch


@pytest.mark.django_db
def test_workspacedetail_post_archived_workspace(rf):
    workspace = WorkspaceFactory(is_archived=True)

    request = rf.post(MEANINGLESS_URL)
    request.session = "session"
    request._messages = FallbackStorage(request)
    request.user = UserFactory()

    response = WorkspaceDetail.as_view()(request, name=workspace.name)

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

    dummy_project = [{"name": "twiddle", "needs": []}]
    with patch("jobserver.views.get_actions", new=lambda *args: dummy_project), patch(
        "jobserver.views.get_branch_sha", new=lambda r, b: "abc123"
    ):
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

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


@pytest.mark.django_db
def test_workspacenotificationstoggle_success(rf):
    workspace = WorkspaceFactory(will_notify=True)
    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory()

    response = WorkspaceNotificationsToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    workspace.refresh_from_db()

    assert not workspace.will_notify


@pytest.mark.django_db
def test_workspacenotificationstoggle_unknown_workspace(rf):
    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory()

    with pytest.raises(Http404):
        WorkspaceNotificationsToggle.as_view()(request, name="test")


@pytest.mark.django_db
def test_workspaceunarchive_already_unarchived(rf):
    workspace = WorkspaceFactory(is_archived=False)

    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory()

    response = WorkspaceUnarchive.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == "/"

    workspace.refresh_from_db()
    assert not workspace.is_archived


@pytest.mark.django_db
def test_workspaceunarchive_success(rf):
    workspace = WorkspaceFactory(is_archived=True)

    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory()

    response = WorkspaceUnarchive.as_view()(request, name=workspace.name)
    assert response.status_code == 302
    assert response.url == "/"
    workspace.refresh_from_db()
    assert not workspace.is_archived
