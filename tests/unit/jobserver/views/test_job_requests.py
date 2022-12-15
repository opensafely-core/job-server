import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import BadRequest
from django.http import Http404
from django.utils import timezone

from jobserver import honeycomb
from jobserver.authorization import (
    CoreDeveloper,
    OpensafelyInteractive,
    ProjectDeveloper,
)
from jobserver.models import JobRequest
from jobserver.views.job_requests import (
    JobRequestCancel,
    JobRequestCreate,
    JobRequestDetail,
    JobRequestDetailRedirect,
    JobRequestList,
    JobRequestPickRef,
)

from ....factories import (
    BackendFactory,
    BackendMembershipFactory,
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
    UserSocialAuthFactory,
    WorkspaceFactory,
)
from ....fakes import FakeGitHubAPI


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

    response = JobRequestCancel.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    job_request.refresh_from_db()
    assert "test1" in job_request.cancelled_actions
    assert "test2" in job_request.cancelled_actions
    assert "test3" in job_request.cancelled_actions


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

    response = JobRequestCancel.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    job_request.refresh_from_db()
    assert sorted(job_request.cancelled_actions) == ["test3", "test4"]


def test_jobrequestcancel_with_job_request_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(cancelled_actions=[], created_by=user)
    JobFactory(job_request=job_request, action="test1")

    request = rf.post("/")
    request.user = user

    response = JobRequestCancel.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    job_request.refresh_from_db()
    assert "test1" in job_request.cancelled_actions


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
        run: test
        outputs:
          moderately_sensitive:
            cohort: /path/to/output.csv
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
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
        ref=ref,
    )

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": []},
        {"name": "run_all", "needs": ["twiddle"]},
    ]
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
            org_slug=workspace.project.org.slug,
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
        run: test
        outputs:
          moderately_sensitive:
            cohort: /path/to/output.csv
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
        org_slug=workspace.project.org.slug,
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
        org_slug=workspace.project.org.slug,
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
        org_slug=workspace.project.org.slug,
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
        run: test
        outputs:
          moderately_sensitive:
            cohort: /path/to/output.csv
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
        org_slug=workspace.project.org.slug,
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
        org_slug=workspace.project.org.slug,
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
        run: test
        outputs:
          moderately_sensitive:
            cohort: /path/to/output.csv
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
        org_slug=workspace.project.org.slug,
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
        run: test
        outputs:
          moderately_sensitive:
            cohort: /path/to/output.csv
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
        org_slug=workspace.project.org.slug,
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
        org_slug=org.slug,
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
        org_slug=workspace.project.org.slug,
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
            org_slug=workspace.project.org.slug,
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
            org_slug=workspace.project.org.slug,
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
        org_slug=job_request.workspace.project.org.slug,
        project_slug=job_request.workspace.project.slug,
        workspace_slug=job_request.workspace.name,
        pk=job_request.pk,
    )

    assert response.status_code == 200
    assert "Cancel" in response.rendered_content


def test_jobrequestdetail_with_permission(rf):
    job_request = JobRequestFactory()

    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    response = JobRequestDetail.as_view()(
        request,
        org_slug=job_request.workspace.project.org.slug,
        project_slug=job_request.workspace.project.slug,
        workspace_slug=job_request.workspace.name,
        pk=job_request.pk,
    )

    assert response.status_code == 200
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
        org_slug=job_request.workspace.project.org.slug,
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
        org_slug=job_request.workspace.project.org.slug,
        project_slug=job_request.workspace.project.slug,
        workspace_slug=job_request.workspace.name,
        pk=job_request.pk,
    )

    assert response.status_code == 200
    assert "Cancel" in response.rendered_content


def test_jobrequestdetail_with_unauthenticated_user(rf):
    job_request = JobRequestFactory()

    request = rf.get("/")
    request.user = AnonymousUser()

    response = JobRequestDetail.as_view()(
        request,
        org_slug=job_request.workspace.project.org.slug,
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
            org_slug=workspace.project.org.slug,
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
        org_slug=job_request.workspace.project.org.slug,
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


def test_jobrequestlist_filters_exist(rf):
    # Build a RequestFactory instance
    request = rf.get("/")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert "statuses" in response.context_data
    assert "workspaces" in response.context_data


def test_jobrequestlist_filter_by_backend(rf):
    backend1 = BackendFactory()
    job_request = JobRequestFactory(backend=backend1)
    JobFactory.create_batch(2, job_request=job_request)

    backend2 = BackendFactory()
    job_request = JobRequestFactory(backend=backend2)
    JobFactory.create_batch(2, job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(f"/?backend={backend1.pk}")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["page_obj"]) == 1


def test_jobrequestlist_filter_by_backend_with_broken_pk(rf):
    request = rf.get("/?backend=test")
    request.user = UserFactory()

    with pytest.raises(BadRequest):
        JobRequestList.as_view()(request)


def test_jobrequestlist_filter_by_status(rf):
    JobFactory(job_request=JobRequestFactory(), status="failed")

    JobFactory(job_request=JobRequestFactory(), status="succeeded")

    # Build a RequestFactory instance
    request = rf.get("/?status=succeeded")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["page_obj"]) == 1


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
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


def test_jobrequestlist_filter_by_unknown_status(rf):
    workspace = WorkspaceFactory()
    JobRequestFactory(workspace=workspace)
    JobRequestFactory(workspace=workspace)

    # Build a RequestFactory instance
    request = rf.get("/?status=test")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert response.status_code == 200

    output = set(response.context_data["object_list"])
    expected = set(JobRequest.objects.all())
    assert output == expected


def test_jobrequestlist_filter_by_username(rf):
    user = UserFactory()
    JobRequestFactory(created_by=user)
    JobRequestFactory(created_by=UserFactory())

    # Build a RequestFactory instance
    request = rf.get(f"/?username={user.username}")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


def test_jobrequestlist_filter_by_workspace(rf):
    workspace = WorkspaceFactory()
    JobRequestFactory(workspace=workspace)
    JobRequestFactory()

    # Build a RequestFactory instance
    request = rf.get(f"/?workspace={workspace.pk}")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


def test_jobrequestlist_filter_by_workspace_with_broken_pk(rf):
    request = rf.get("/?workspace=test")
    request.user = UserFactory()

    with pytest.raises(BadRequest):
        JobRequestList.as_view()(request)


def test_jobrequestlist_find_job_request_by_identifier_form_invalid(rf):
    request = rf.post("/", {"test-key": "test-value"})
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert response.status_code == 200

    expected = {"identifier": ["This field is required."]}
    assert response.context_data["form"].errors == expected


def test_jobrequestlist_find_job_request_by_identifier_success(rf):
    job_request = JobRequestFactory(identifier="test-identifier")

    request = rf.post("/", {"identifier": job_request.identifier})
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()


def test_jobrequestlist_find_job_request_by_identifier_unknown_job_request(rf):
    request = rf.post("/", {"identifier": "test-value"})
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert response.status_code == 200

    expected = {
        "identifier": ["Could not find a JobRequest with the identfier 'test-value'"],
    }
    assert response.context_data["form"].errors == expected


def test_jobrequestlist_search_by_action(rf):
    job_request1 = JobRequestFactory()
    JobFactory(job_request=job_request1, action="run")

    job_request2 = JobRequestFactory()
    JobFactory(job_request=job_request2, action="leap")

    # Build a RequestFactory instance
    request = rf.get("/?q=run")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request1


def test_jobrequestlist_search_by_id(rf):
    JobFactory(job_request=JobRequestFactory())

    job_request2 = JobRequestFactory()
    JobFactory(job_request=job_request2, id=99)

    # Build a RequestFactory instance
    request = rf.get("/?q=99")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request2


def test_jobrequestlist_success(rf):
    user = UserSocialAuthFactory().user

    job_request = JobRequestFactory(created_by=user)
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get("/")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request

    assert response.context_data["users"] == {user.username: user.name}
    assert len(response.context_data["workspaces"]) == 1


def test_jobrequestlist_with_core_developer(rf, core_developer):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request)

    request = rf.get("/")
    request.user = core_developer
    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert "Look up JobRequest by Identifier" in response.rendered_content


def test_jobrequestlist_with_permission(rf):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request)
    request = rf.get("/")
    request.user = UserFactory(roles=[])
    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert "Look up JobRequest by Identifier" not in response.rendered_content


def test_jobrequestlist_without_permission(rf):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request)

    request = rf.get("/")
    request.user = AnonymousUser()
    response = JobRequestList.as_view()(request)
    assert response.status_code == 200
    assert "Look up JobRequest by Identifier" not in response.rendered_content


def test_jobrequestpickref_success(rf):
    user = UserFactory(roles=[OpensafelyInteractive])
    BackendMembershipFactory(user=user)
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = user

    response = JobRequestPickRef.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["commits"] == [
        {"message": "I am a short message title", "sha": "abc123"}
    ]


def test_jobrequestpickref_unauthorized(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = JobRequestPickRef.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_jobs_url()


def test_jobrequestpickref_with_archived_workspace(rf):
    workspace = WorkspaceFactory(is_archived=True)

    request = rf.get("/")
    request.user = UserFactory(roles=[OpensafelyInteractive])

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = JobRequestPickRef.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1

    expected = (
        "You cannot create Jobs for an archived Workspace."
        "Please contact an admin if you need to have it unarchved."
    )
    assert str(messages[0]) == expected


def test_jobrequestpickref_get_with_all_backends_removed(rf, settings, user):
    settings.DISABLE_CREATING_JOBS = True

    user = UserFactory(roles=[OpensafelyInteractive])
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=BackendFactory(slug="tpp"), user=user)
    BackendMembershipFactory(backend=BackendFactory(slug="emis"), user=user)

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        JobRequestPickRef.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


def test_jobrequestpickref_with_commits_error(rf):
    user = UserFactory(roles=[OpensafelyInteractive])
    BackendMembershipFactory(user=user)
    workspace = WorkspaceFactory()

    class BrokenGitHubAPI:
        def __init__(self):
            raise Exception()

    request = rf.get("/")
    request.user = user

    response = JobRequestPickRef.as_view(get_github_api=BrokenGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert "error" in response.context_data


def test_jobrequestpickref_with_no_backends(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[OpensafelyInteractive])

    with pytest.raises(Http404):
        JobRequestPickRef.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


def test_jobrequestpickref_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        JobRequestPickRef.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )
