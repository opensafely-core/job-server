from datetime import timedelta
from unittest.mock import patch

import pytest
import responses
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from first import first

from jobserver.models import Backend, JobRequest, Org, Project, Workspace
from jobserver.views import (
    BackendDetail,
    BackendList,
    BackendRotateToken,
    Index,
    JobCancel,
    JobDetail,
    JobRequestList,
    JobRequestZombify,
    JobZombify,
    OrgCreate,
    OrgDetail,
    OrgList,
    ProjectCreate,
    ProjectDetail,
    Settings,
    Status,
    WorkspaceArchiveToggle,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceLog,
    WorkspaceNotificationsToggle,
    WorkspaceReleaseView,
)

from ..factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    OrgFactory,
    ProjectFactory,
    StatsFactory,
    UserFactory,
    UserSocialAuthFactory,
    WorkspaceFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_backenddetail_success(rf, superuser):
    backend = BackendFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = BackendDetail.as_view()(request, pk=backend.pk)

    assert response.status_code == 200
    assert response.context_data["backend"] == backend


@pytest.mark.django_db
def test_backendlist_success(rf, superuser):
    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = BackendList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 3


@pytest.mark.django_db
def test_backendrotatetoken_success(rf, superuser):
    backend = BackendFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = superuser
    response = BackendRotateToken.as_view()(request, pk=backend.pk)

    assert response.status_code == 302
    assert response.url == reverse("backend-detail", kwargs={"pk": backend.pk})


@pytest.mark.django_db
def test_index_success(rf):
    JobRequestFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True):
        response = Index.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["job_requests"]) == 1
    assert len(response.context_data["workspaces"]) == 1


@pytest.mark.django_db
def test_index_with_authenticated_user(rf):
    """
    Check the Add Workspace button is rendered for authenticated Users on the
    homepage.
    """
    JobRequestFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True):
        response = Index.as_view()(request)

    assert "Add a New Workspace" in response.rendered_content


@pytest.mark.django_db
def test_index_with_authenticated_but_partially_registered_user(rf):
    """
    Check the Add Workspace button is rendered for authenticated Users on the
    homepage.
    """
    JobRequestFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    with patch("jobserver.views.can_run_jobs", return_value=False, autospec=True):
        response = Index.as_view()(request)

    assert "Add a New Workspace" not in response.rendered_content


@pytest.mark.django_db
def test_index_with_unauthenticated_user(rf):
    """
    Check the Add Workspace button is not rendered for unauthenticated Users on
    the homepage.
    """
    JobRequestFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()
    response = Index.as_view()(request)

    assert "Add a New Workspace" not in response.rendered_content


@pytest.mark.django_db
@responses.activate
def test_jobcancel_already_cancelled(rf):
    job_request = JobRequestFactory(cancelled_actions=["another-action", "test"])
    job = JobFactory(job_request=job_request, action="test")

    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action", "test"]


@pytest.mark.django_db
@responses.activate
def test_jobcancel_already_finished(rf):
    job_request = JobRequestFactory(cancelled_actions=["another-action"])
    job = JobFactory(job_request=job_request, action="test", status="finished")

    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action", "test"]


@pytest.mark.django_db
@responses.activate
def test_jobcancel_success(rf):
    job_request = JobRequestFactory(cancelled_actions=[])
    job = JobFactory(job_request=job_request, action="test")

    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["test"]


@pytest.mark.django_db
@responses.activate
def test_jobcancel_unauthorized(rf):
    job = JobFactory(job_request=JobRequestFactory())
    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
@responses.activate
def test_jobcancel_unknown_job(rf):
    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    with pytest.raises(Http404):
        JobCancel.as_view()(request, identifier="not-real")


@pytest.mark.django_db
def test_jobdetail_with_post_jobrequest_job(rf):
    job = JobFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    with patch("jobserver.views.can_run_jobs", return_value=False):
        response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_pre_jobrequest_job(rf):
    job_request = JobRequestFactory(workspace=WorkspaceFactory())
    job = JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    with patch("jobserver.views.can_run_jobs", return_value=False):
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

    client.force_login(UserFactory(roles=[]))
    with patch("jobserver.views.can_run_jobs", return_value=False):
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
def test_jobzombify_success(rf, superuser):
    job = JobFactory(completed_at=None)

    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

    response = JobZombify.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job.refresh_from_db()

    assert job.status == "failed"
    assert job.status_message == "Job manually zombified"


@pytest.mark.django_db
def test_jobzombify_unknown_job(rf, superuser):
    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

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
def test_jobrequestlist_filter_by_backend(rf):
    emis = Backend.objects.get(name="emis")
    job_request = JobRequestFactory(backend=emis)
    JobFactory.create_batch(2, job_request=job_request)

    tpp = Backend.objects.get(name="tpp")
    job_request = JobRequestFactory(backend=tpp)
    JobFactory.create_batch(2, job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(f"/?backend={emis.pk}")
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["page_obj"]) == 1


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
def test_jobrequestlist_find_job_request_by_identifier_form_invalid(rf):
    request = rf.post(MEANINGLESS_URL, {"test-key": "test-value"})
    response = JobRequestList.as_view()(request)

    assert response.status_code == 200

    expected = {"identifier": ["This field is required."]}
    assert response.context_data["form"].errors == expected


@pytest.mark.django_db
def test_jobrequestlist_find_job_request_by_identifier_success(rf):
    job_request = JobRequestFactory(identifier="test-identifier")

    request = rf.post(MEANINGLESS_URL, {"identifier": job_request.identifier})
    response = JobRequestList.as_view()(request)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()


@pytest.mark.django_db
def test_jobrequestlist_find_job_request_by_identifier_unknown_job_request(rf):
    request = rf.post(MEANINGLESS_URL, {"identifier": "test-value"})
    response = JobRequestList.as_view()(request)

    assert response.status_code == 200

    expected = {
        "identifier": ["Could not find a JobRequest with the identfier 'test-value'"],
    }
    assert response.context_data["form"].errors == expected


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

    client.force_login(UserFactory(roles=[]))
    response = client.post(f"/job-requests/{job_request.pk}/zombify/", follow=True)

    assert response.status_code == 200

    # did we redirect to the correct JobDetail page?
    assert response.redirect_chain == [(job_request.get_absolute_url(), 302)]

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
def test_jobrequestzombify_success(rf, superuser):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request, completed_at=None)

    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

    response = JobRequestZombify.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    jobs = job_request.jobs.all()

    assert all(j.status == "failed" for j in jobs)
    assert all(j.status_message == "Job manually zombified" for j in jobs)


@pytest.mark.django_db
def test_jobrequestzombify_unknown_jobrequest(rf, superuser):
    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        JobRequestZombify.as_view()(request, pk="99")


@pytest.mark.django_db
def test_orgcreate_get_success(rf, superuser):
    oxford = OrgFactory(name="University of Oxford")
    datalab = OrgFactory(name="DataLab")

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = OrgCreate.as_view()(request)

    assert response.status_code == 200

    orgs = response.context_data["orgs"]
    assert len(orgs) == 2
    assert orgs[0] == datalab
    assert orgs[1] == oxford


@pytest.mark.django_db
def test_orgcreate_post_success(rf, superuser):
    request = rf.post(MEANINGLESS_URL, {"name": "A New Org"})
    request.user = superuser
    response = OrgCreate.as_view()(request)

    assert response.status_code == 302

    orgs = Org.objects.all()
    assert len(orgs) == 1

    org = orgs.first()
    assert org.name == "A New Org"
    assert response.url == org.get_absolute_url()


@pytest.mark.django_db
def test_orgdetail_success(rf, superuser):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = OrgDetail.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200


@pytest.mark.django_db
def test_orgdetail_unknown_org(rf, superuser):
    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        OrgDetail.as_view()(request, org_slug="")


@pytest.mark.django_db
def test_orglist_success(rf, superuser):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = OrgList.as_view()(request)

    assert response.status_code == 200
    assert org in response.context_data["object_list"]


@pytest.mark.django_db
def test_projectcreate_get_success(rf, superuser):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = ProjectCreate.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200


@pytest.mark.django_db
def test_projectcreate_get_unknown_org(rf, superuser):
    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectCreate.as_view()(request, org_slug="")


@pytest.mark.django_db
def test_projectcreate_post_invalid_data(rf, superuser):
    org = OrgFactory()

    data = {
        "name": "",
        "project_lead": "",
        "email": "",
        "researcher-TOTAL_FORMS": "0",
        "researcher-INITIAL_FORMS": "0",
        "researcher-MIN_NUM": "0",
        "researcher-MAX_NUM": "1000",
    }

    request = rf.post(MEANINGLESS_URL, data)
    request.user = superuser
    response = ProjectCreate.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200
    assert Project.objects.count() == 0


@pytest.mark.django_db
def test_projectcreate_post_success(rf, superuser):
    org = OrgFactory()

    data = {
        "name": "A Brand New Project",
        "project_lead": "My Name",
        "email": "name@example.com",
        "researcher-TOTAL_FORMS": "1",
        "researcher-INITIAL_FORMS": "0",
        "researcher-MIN_NUM": "0",
        "researcher-MAX_NUM": "1000",
        "researcher-0-name": "Test",
        "researcher-0-passed_researcher_training_at": "2021-01-01",
        "researcher-0-is_ons_accredited_researcher": "on",
    }

    request = rf.post(MEANINGLESS_URL, data)
    request.user = superuser
    response = ProjectCreate.as_view()(request, org_slug=org.slug)

    assert response.status_code == 302

    projects = Project.objects.all()
    assert len(projects) == 1

    project = projects.first()
    assert project.name == "A Brand New Project"
    assert project.project_lead == "My Name"
    assert project.email == "name@example.com"
    assert project.org == org
    assert response.url == project.get_absolute_url()


@pytest.mark.django_db
def test_projectcreate_post_unknown_org(rf, superuser):
    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectCreate.as_view()(request, org_slug="")


@pytest.mark.django_db
def test_projectdetail_success(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = ProjectDetail.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_projectdetail_unknown_org(rf, superuser):
    project = ProjectFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectDetail.as_view()(request, org_slug="test", project_slug=project.slug)


@pytest.mark.django_db
def test_projectdetail_unknown_project(rf, superuser):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectDetail.as_view()(request, org_slug=org.slug, project_slug="test")


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

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = Settings.as_view()(request)
    assert response.status_code == 302
    assert response.url == "/"

    user2.refresh_from_db()

    assert user2.notifications_email == "changed@example.com"

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Settings saved successfully"


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

    with patch("jobserver.views.get_repos_with_branches", new=lambda *args: []):
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
    with patch("jobserver.views.get_repos_with_branches", new=lambda *args: repos):
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

    with patch("jobserver.views.get_actions", autospec=True) as mocked_get_actions:
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

    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True), patch(
        "jobserver.views.get_project",
        side_effect=Exception("test error"),
        autospec=True,
    ):
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

    dummy_yaml = """
    actions:
      twiddle:
    """
    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True), patch(
        "jobserver.views.get_project", new=lambda *args: dummy_yaml
    ):
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

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

    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True), patch(
        "jobserver.views.get_actions", return_value=[], autospec=True
    ):
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

    dummy_yaml = """
    actions:
      twiddle:
    """
    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True), patch(
        "jobserver.views.get_project", new=lambda *args: dummy_yaml
    ), patch("jobserver.views.get_branch_sha", new=lambda r, b: "abc123"):
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
    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True), patch(
        "jobserver.views.get_project", new=lambda *args: dummy_yaml
    ), patch("jobserver.views.get_branch_sha", new=lambda r, b: "abc123"):
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

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
    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True), patch(
        "jobserver.views.get_project", new=lambda *args: dummy_yaml
    ), patch("jobserver.views.get_branch_sha", new=lambda r, b: "abc123"):
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

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
    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True), patch(
        "jobserver.views.get_project", new=lambda *args: dummy_yaml
    ), patch("jobserver.views.get_branch_sha", new=lambda r, b: "abc123"):
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

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
def test_workspacedetail_unknown_workspace(rf):
    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = WorkspaceDetail.as_view()(request, name="test")

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_workspacedetail_get_with_authenticated_user(rf):
    """
    Check WorkspaceDetail renders the controls for Archiving, Notifications,
    and selecting Actions for authenticated Users.
    """
    workspace = WorkspaceFactory(is_archived=False)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    dummy_yaml = """
    actions:
      twiddle:
    """
    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True), patch(
        "jobserver.views.get_project", new=lambda *args: dummy_yaml
    ):
        response = WorkspaceDetail.as_view()(request, name=workspace.name)

    assert "Archive" in response.rendered_content
    assert "Turn Notifications" in response.rendered_content
    assert "twiddle" in response.rendered_content


@pytest.mark.django_db
def test_workspacedetail_get_with_unauthenticated_user(rf):
    """
    Check WorkspaceDetail does not render the controls for Archiving,
    Notifications, and selecting Actions for unauthenticated Users.
    """
    workspace = WorkspaceFactory(is_archived=False)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()
    response = WorkspaceDetail.as_view()(request, name=workspace.name)

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

    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True):
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

    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True):
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

    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True):
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

    with patch("jobserver.views.can_run_jobs", return_value=True, autospec=True):
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
