import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.utils import timezone

from jobserver import honeycomb
from jobserver.authorization import CoreDeveloper, ProjectDeveloper
from jobserver.models import JobRequest
from jobserver.utils import set_from_qs
from jobserver.views.job_requests import (
    JobRequestCancel,
    JobRequestCreate,
    JobRequestDetail,
    JobRequestDetailRedirect,
    JobRequestList,
)

from ....factories import (
    BackendFactory,
    BackendMembershipFactory,
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
    WorkspaceFactory,
)
from ....fakes import FakeGitHubAPI
from ....utils import minutes_ago


def test_jobrequestcancel_already_completed(rf):
    job_request = JobRequestFactory(cancelled_actions=[])
    JobFactory(job_request=job_request, status="succeeded")
    JobFactory(job_request=job_request, status="failed")
    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post("/")
    request.user = user

    response = JobRequestCancel.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == []


def test_jobrequestcancel_success(rf):
    job_request = JobRequestFactory(cancelled_actions=[])
    JobFactory(job_request=job_request, action="test1")
    JobFactory(job_request=job_request, action="test2")
    JobFactory(job_request=job_request, action="test3")
    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post("/")
    request.user = user

    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = JobRequestCancel.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    job_request.refresh_from_db()
    assert "test1" in job_request.cancelled_actions
    assert "test2" in job_request.cancelled_actions
    assert "test3" in job_request.cancelled_actions

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "The requested actions have been cancelled"


def test_jobrequestcancel_partially_completed(rf):
    job_request = JobRequestFactory(cancelled_actions=[])
    JobFactory(job_request=job_request, action="test1", status="failed")
    JobFactory(job_request=job_request, action="test2", status="succeeded")
    JobFactory(job_request=job_request, action="test3", status="running")
    JobFactory(job_request=job_request, action="test4", status="pending")

    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post("/")
    request.user = user

    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = JobRequestCancel.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    job_request.refresh_from_db()
    assert sorted(job_request.cancelled_actions) == ["test3", "test4"]

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "The requested actions have been cancelled"


def test_jobrequestcancel_with_job_request_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(cancelled_actions=[], created_by=user)
    JobFactory(job_request=job_request, action="test1")

    request = rf.post("/")
    request.user = user

    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = JobRequestCancel.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    job_request.refresh_from_db()
    assert "test1" in job_request.cancelled_actions

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "The requested actions have been cancelled"


def test_jobrequestcancel_unauthorized(rf):
    job_request = JobRequestFactory()
    user = UserFactory()

    request = rf.post("/")
    request.user = user

    with pytest.raises(Http404):
        JobRequestCancel.as_view()(request, pk=job_request.pk)


def test_jobrequestcancel_unknown_job_request(rf):
    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        JobRequestCancel.as_view()(request, pk=0)


@pytest.mark.parametrize("ref", [None, "abc"])
def test_jobrequestcreate_get_success(ref, rf, mocker, user):
    now = timezone.now()
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(
        job_request=job_request,
        started_at=minutes_ago(now, 3),
        completed_at=minutes_ago(now, 1),
    )

    BackendMembershipFactory(user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    dummy_yaml = """
    version: 3
    expectations:
      population_size: 1000
    actions:
      twiddle:
        run: test:latest
        outputs:
          moderately_sensitive:
            cohort: path/to/output.csv
    """
    mocker.patch(
        "jobserver.views.job_requests.get_project",
        autospec=True,
        return_value=dummy_yaml,
    )

    request = rf.get("/")
    request.user = user

    response = JobRequestCreate.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
        ref=ref,
    )

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": []},
        {"name": "run_all", "needs": ["twiddle"]},
    ]
    assert response.context_data["latest_job_request"] == job_request
    assert response.context_data["workspace"] == workspace


def test_jobrequestcreate_get_with_all_backends_removed(rf, settings, user):
    settings.DISABLE_CREATING_JOBS = True

    tpp = BackendFactory(slug="tpp")
    emis = BackendFactory(slug="emis")
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=tpp, user=user)
    BackendMembershipFactory(backend=emis, user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        JobRequestCreate.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


def test_jobrequestcreate_get_with_permission(rf, mocker, user):
    workspace = WorkspaceFactory()

    BackendMembershipFactory(user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    dummy_yaml = """
    version: 3
    expectations:
      population_size: 1000
    actions:
      twiddle:
        run: test:latest
        outputs:
          moderately_sensitive:
            cohort: path/to/output.csv
    """
    mocker.patch(
        "jobserver.views.job_requests.get_project",
        autospec=True,
        return_value=dummy_yaml,
    )

    request = rf.get("/")
    request.user = user

    response = JobRequestCreate.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": []},
        {"name": "run_all", "needs": ["twiddle"]},
    ]
    assert response.context_data["workspace"] == workspace


def test_jobrequestcreate_get_with_project_yaml_errors(rf, mocker, user):
    workspace = WorkspaceFactory()

    BackendMembershipFactory(user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    mocker.patch(
        "jobserver.views.job_requests.get_project",
        autospec=True,
        side_effect=Exception("test error"),
    )

    request = rf.get("/")
    request.user = user

    response = JobRequestCreate.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["actions"] == []
    assert response.context_data["actions_error"] == "test error"


def test_jobrequestcreate_get_with_some_backends_removed(rf, mocker, settings, user):
    settings.DISABLE_CREATING_JOBS = True

    backend = BackendFactory()
    emis = BackendFactory(slug="emis")
    tpp = BackendFactory(slug="tpp")

    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend, user=user)
    BackendMembershipFactory(backend=emis, user=user)
    BackendMembershipFactory(backend=tpp, user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.job_requests.get_project",
        autospec=True,
        return_value=dummy_yaml,
    )

    request = rf.get("/")
    request.user = user

    response = JobRequestCreate.as_view(get_github_api=FakeGitHubAPI)(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    # confirm we only have the one remaining backend in the form here
    assert response.context_data["form"]["backend"].field.choices == [
        (backend.slug, backend.name)
    ]


@pytest.mark.parametrize("ref", [None, "abc"])
def test_jobrequestcreate_post_success(ref, rf, mocker, monkeypatch, user):
    backend = BackendFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend, user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    dummy_yaml = """
    version: 3
    expectations:
      population_size: 1000
    actions:
      twiddle:
        run: test:latest
        outputs:
          moderately_sensitive:
            cohort: path/to/output.csv
    """
    mocker.patch(
        "jobserver.views.job_requests.get_project",
        autospec=True,
        return_value=dummy_yaml,
    )

    data = {
        "backend": backend.slug,
        "requested_actions": ["twiddle"],
        "callback_url": "test",
    }
    request = rf.post("/", data)
    request.user = user

    response = JobRequestCreate.as_view(get_github_api=FakeGitHubAPI)(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
        ref=ref,
    )

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == workspace.get_logs_url()

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend.slug == backend.slug
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == ref or "abc123"
    assert not job_request.jobs.exists()


def test_jobrequestcreate_post_with_invalid_backend(rf, mocker, monkeypatch, user):
    backend1 = BackendFactory()
    backend2 = BackendFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend1, user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.job_requests.get_project",
        autospec=True,
        return_value=dummy_yaml,
    )

    data = {
        "backend": backend2.slug,
        "requested_actions": ["twiddle"],
        "callback_url": "test",
    }
    request = rf.post("/", data)
    request.user = user

    response = JobRequestCreate.as_view(get_github_api=FakeGitHubAPI)(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["form"].errors["backend"] == [
        f"Select a valid choice. {backend2.slug} is not one of the available choices."
    ]


def test_jobrequestcreate_post_with_notifications_default(
    rf, mocker, monkeypatch, user
):
    backend = BackendFactory()
    workspace = WorkspaceFactory(should_notify=True)

    BackendMembershipFactory(backend=backend, user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    dummy_yaml = """
    version: 3
    expectations:
      population_size: 1000
    actions:
      twiddle:
        run: test:latest
        outputs:
          moderately_sensitive:
            cohort: path/to/output.csv
    """
    mocker.patch(
        "jobserver.views.job_requests.get_project",
        autospec=True,
        return_value=dummy_yaml,
    )

    data = {
        "backend": backend.slug,
        "requested_actions": ["twiddle"],
        "callback_url": "test",
        "will_notify": "True",
    }
    request = rf.post("/", data)
    request.user = user

    response = JobRequestCreate.as_view(get_github_api=FakeGitHubAPI)(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == workspace.get_logs_url()

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend.slug == backend.slug
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert job_request.will_notify


def test_jobrequestcreate_post_with_notifications_override(
    rf, mocker, monkeypatch, user
):
    backend = BackendFactory()
    workspace = WorkspaceFactory(should_notify=True)

    BackendMembershipFactory(backend=backend, user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    dummy_yaml = """
    version: 3
    expectations:
      population_size: 1000
    actions:
      twiddle:
        run: test:latest
        outputs:
          moderately_sensitive:
            cohort: path/to/output.csv
    """
    mocker.patch(
        "jobserver.views.job_requests.get_project",
        autospec=True,
        return_value=dummy_yaml,
    )

    data = {
        "backend": backend.slug,
        "requested_actions": ["twiddle"],
        "callback_url": "test",
        "will_notify": "False",
    }
    request = rf.post("/", data)
    request.user = user

    response = JobRequestCreate.as_view(get_github_api=FakeGitHubAPI)(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == workspace.get_logs_url()

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend.slug == backend.slug
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert not job_request.will_notify
    assert not job_request.jobs.exists()


def test_jobrequestcreate_unknown_workspace(rf, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)

    request = rf.get("/")
    request.user = user
    response = JobRequestCreate.as_view()(
        request,
        project_slug=project.slug,
        workspace_slug="test",
    )

    assert response.status_code == 302
    assert response.url == "/"


def test_jobrequestcreate_with_archived_workspace(rf):
    user = UserFactory()
    workspace = WorkspaceFactory(is_archived=True)

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.session = "session"
    request._messages = FallbackStorage(request)
    request.user = user

    response = JobRequestCreate.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()


def test_jobrequestcreate_with_no_backends(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        JobRequestCreate.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


def test_jobrequestcreate_without_permission(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        JobRequestCreate.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


def test_jobrequestdetail_with_job_request_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(created_by=user)

    request = rf.get("/")
    request.user = user

    response = JobRequestDetail.as_view()(
        request,
        project_slug=job_request.workspace.project.slug,
        workspace_slug=job_request.workspace.name,
        pk=job_request.pk,
    )

    assert response.status_code == 200
    assert "Cancel" in response.rendered_content


def test_jobrequestdetail_with_invalid_job_request(rf, django_assert_num_queries):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, action="__error__")

    request = rf.get("/")
    request.user = UserFactory()

    response = JobRequestDetail.as_view()(
        request,
        project_slug=job_request.workspace.project.slug,
        workspace_slug=job_request.workspace.name,
        pk=job_request.pk,
    )

    assert response.status_code == 200
    assert response.context_data["is_invalid"]


def test_jobrequestdetail_with_permission(rf, django_assert_num_queries):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, updated_at=minutes_ago(timezone.now(), 31))

    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    with django_assert_num_queries(6):
        response = JobRequestDetail.as_view()(
            request,
            project_slug=job_request.workspace.project.slug,
            workspace_slug=job_request.workspace.name,
            pk=job_request.pk,
        )

    assert response.status_code == 200
    assert not response.context_data["is_invalid"]
    assert response.context_data["is_missing_updates"]
    assert "Cancel" in response.rendered_content


@pytest.mark.freeze_time("2022-06-16 12:00")
def test_jobrequestdetail_with_permission_core_developer(rf):
    job_request = JobRequestFactory()
    job = JobFactory(  # noqa: F841
        job_request=job_request, completed_at=timezone.now(), status="succeeded"
    )

    user = UserFactory(roles=[CoreDeveloper])

    request = rf.get("/")
    request.user = user

    response = JobRequestDetail.as_view()(
        request,
        project_slug=job_request.workspace.project.slug,
        workspace_slug=job_request.workspace.name,
        pk=job_request.pk,
    )

    assert response.status_code == 200
    assert "Honeycomb" in response.rendered_content

    # job_requests have prefetch restrictions on them
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()
    url = honeycomb.jobrequest_link(prefetched_job_request)
    assert url in response.rendered_content


def test_jobrequestdetail_with_permission_with_completed_at(rf):
    job_request = JobRequestFactory()

    JobFactory(
        job_request=job_request,
        status="succeeded",
        completed_at=timezone.now(),
    )

    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    response = JobRequestDetail.as_view()(
        request,
        project_slug=job_request.workspace.project.slug,
        workspace_slug=job_request.workspace.name,
        pk=job_request.pk,
    )

    assert response.status_code == 200
    assert not response.context_data["is_missing_updates"]
    assert "Cancel" in response.rendered_content


def test_jobrequestdetail_with_unauthenticated_user(rf):
    job_request = JobRequestFactory()

    request = rf.get("/")
    request.user = AnonymousUser()

    response = JobRequestDetail.as_view()(
        request,
        project_slug=job_request.workspace.project.slug,
        workspace_slug=job_request.workspace.name,
        pk=job_request.pk,
    )

    assert response.status_code == 200
    assert "Honeycomb" not in response.rendered_content


def test_jobrequestdetail_with_unknown_job_request(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        JobRequestDetail.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk=0,
        )


def test_jobrequestdetail_without_permission(rf):
    job_request = JobRequestFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = JobRequestDetail.as_view()(
        request,
        project_slug=job_request.workspace.project.slug,
        workspace_slug=job_request.workspace.name,
        pk=job_request.pk,
    )

    assert response.status_code == 200
    assert "Cancel" not in response.rendered_content


def test_jobrequestdetailredirect_success(rf):
    job_request = JobRequestFactory()

    request = rf.get("/")

    response = JobRequestDetailRedirect.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()


def test_jobrequestdetailredirect_with_unknown_job(rf):
    request = rf.get("/")

    with pytest.raises(Http404):
        JobRequestDetailRedirect.as_view()(request, pk=0)


def test_jobrequestlist_success(rf):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request)

    request = rf.get("/")
    request.user = UserFactory()

    response = JobRequestList.as_view()(request)

    assert set_from_qs(response.context_data["object_list"]) == {job_request.pk}
