import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import BadRequest
from django.http import Http404

from jobserver.authorization import ProjectDeveloper
from jobserver.models import Backend, JobRequest
from jobserver.views.job_requests import (
    JobRequestCancel,
    JobRequestCreate,
    JobRequestDetail,
    JobRequestDetailRedirect,
    JobRequestList,
)

from ....factories import (
    BackendMembershipFactory,
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
    UserSocialAuthFactory,
    WorkspaceFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_jobrequestcancel_already_completed(rf):
    job_request = JobRequestFactory(cancelled_actions=[])
    JobFactory(job_request=job_request, status="succeeded")
    JobFactory(job_request=job_request, status="failed")
    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    response = JobRequestCancel.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == []


@pytest.mark.django_db
def test_jobrequestcancel_success(rf):
    job_request = JobRequestFactory(cancelled_actions=[])
    JobFactory(job_request=job_request, action="test1")
    JobFactory(job_request=job_request, action="test2")
    JobFactory(job_request=job_request, action="test3")
    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    response = JobRequestCancel.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    job_request.refresh_from_db()
    assert "test1" in job_request.cancelled_actions
    assert "test2" in job_request.cancelled_actions
    assert "test3" in job_request.cancelled_actions


@pytest.mark.django_db
def test_jobrequestcancel_with_job_request_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(cancelled_actions=[], created_by=user)
    JobFactory(job_request=job_request, action="test1")

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    response = JobRequestCancel.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()

    job_request.refresh_from_db()
    assert "test1" in job_request.cancelled_actions


@pytest.mark.django_db
def test_jobrequestcancel_unauthorized(rf):
    job_request = JobRequestFactory()
    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    with pytest.raises(Http404):
        JobRequestCancel.as_view()(request, pk=job_request.pk)


@pytest.mark.django_db
def test_jobrequestcancel_unknown_job_request(rf):
    request = rf.post(MEANINGLESS_URL)
    request.user = UserFactory()

    with pytest.raises(Http404):
        JobRequestCancel.as_view()(request, pk=0)


@pytest.mark.django_db
def test_jobrequestcreate_get_with_project_yaml_errors(rf, mocker, user):
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=Backend.objects.get(slug="tpp"), user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    mocker.patch(
        "jobserver.views.job_requests.get_project",
        autospec=True,
        side_effect=Exception("test error"),
    )

    request = rf.get(MEANINGLESS_URL)
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


@pytest.mark.django_db
def test_jobrequestcreate_get_success(rf, mocker, user):
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=Backend.objects.get(slug="tpp"), user=user)
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

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = JobRequestCreate.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": [], "status": "-"},
        {"name": "run_all", "needs": ["twiddle"], "status": "-"},
    ]
    assert response.context_data["workspace"] == workspace


@pytest.mark.django_db
def test_jobrequestcreate_get_with_permission(rf, mocker, user):
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=Backend.objects.get(slug="tpp"), user=user)
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

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = JobRequestCreate.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": [], "status": "-"},
        {"name": "run_all", "needs": ["twiddle"], "status": "-"},
    ]
    assert response.context_data["workspace"] == workspace


@pytest.mark.django_db
def test_jobrequestcreate_post_success(rf, mocker, monkeypatch, user):
    monkeypatch.setenv("BACKENDS", "tpp")

    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=Backend.objects.get(slug="tpp"), user=user)
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
    mocker.patch(
        "jobserver.views.job_requests.get_branch_sha",
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

    response = JobRequestCreate.as_view()(
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
    assert job_request.backend.slug == "tpp"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert not job_request.jobs.exists()


@pytest.mark.django_db
def test_jobrequestcreate_post_with_invalid_backend(rf, mocker, monkeypatch, user):
    monkeypatch.setenv("BACKENDS", "tpp,emis")

    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=Backend.objects.get(slug="tpp"), user=user)
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
    mocker.patch(
        "jobserver.views.job_requests.get_branch_sha",
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

    response = JobRequestCreate.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["form"].errors["backend"] == [
        "Select a valid choice. emis is not one of the available choices."
    ]


@pytest.mark.django_db
def test_jobrequestcreate_post_with_notifications_default(
    rf, mocker, monkeypatch, user
):
    monkeypatch.setenv("BACKENDS", "tpp")

    workspace = WorkspaceFactory(should_notify=True)

    BackendMembershipFactory(backend=Backend.objects.get(slug="tpp"), user=user)
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
    mocker.patch(
        "jobserver.views.job_requests.get_branch_sha",
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

    response = JobRequestCreate.as_view()(
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
    assert job_request.backend.slug == "tpp"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert job_request.will_notify


@pytest.mark.django_db
def test_jobrequestcreate_post_with_notifications_override(
    rf, mocker, monkeypatch, user
):
    monkeypatch.setenv("BACKENDS", "tpp")

    workspace = WorkspaceFactory(should_notify=True)

    BackendMembershipFactory(backend=Backend.objects.get(slug="tpp"), user=user)
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
    mocker.patch(
        "jobserver.views.job_requests.get_branch_sha",
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

    response = JobRequestCreate.as_view()(
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
    assert job_request.backend.slug == "tpp"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert not job_request.will_notify
    assert not job_request.jobs.exists()


@pytest.mark.django_db
def test_jobrequestcreate_unknown_workspace(rf, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)

    request = rf.get(MEANINGLESS_URL)
    request.user = user
    response = JobRequestCreate.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug="test",
    )

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_jobrequestdetail_with_authenticated_user(rf):
    job_request = JobRequestFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = JobRequestDetail.as_view()(request, pk=job_request.pk)

    assert response.status_code == 200
    assert "Cancel" in response.rendered_content


@pytest.mark.django_db
def test_jobrequestdetail_with_job_request_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(created_by=user)

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = JobRequestDetail.as_view()(request, pk=job_request.pk)

    assert response.status_code == 200
    assert "Cancel" in response.rendered_content


@pytest.mark.django_db
def test_jobrequestdetail_with_unauthenticated_user(rf):
    job_request = JobRequestFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()

    response = JobRequestDetail.as_view()(request, pk=job_request.pk)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobrequestdetail_with_unprivileged_user(rf):
    job_request = JobRequestFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    response = JobRequestDetail.as_view()(request, pk=job_request.pk)

    assert response.status_code == 200
    assert "Cancel" not in response.rendered_content


@pytest.mark.django_db
def test_jobrequestdetailredirect_success(rf):
    job_request = JobRequestFactory()

    request = rf.get(MEANINGLESS_URL)

    response = JobRequestDetailRedirect.as_view()(request, pk=job_request.pk)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()


@pytest.mark.django_db
def test_jobrequestdetailredirect_with_unknown_job(rf):
    request = rf.get(MEANINGLESS_URL)

    with pytest.raises(Http404):
        JobRequestDetailRedirect.as_view()(request, pk=0)


@pytest.mark.django_db
def test_jobrequestlist_filters_exist(rf):
    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert "statuses" in response.context_data
    assert "workspaces" in response.context_data


@pytest.mark.django_db
def test_jobrequestlist_filter_by_backend(rf):
    emis = Backend.objects.get(slug="emis")
    job_request = JobRequestFactory(backend=emis)
    JobFactory.create_batch(2, job_request=job_request)

    tpp = Backend.objects.get(slug="tpp")
    job_request = JobRequestFactory(backend=tpp)
    JobFactory.create_batch(2, job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(f"/?backend={emis.pk}")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["page_obj"]) == 1


@pytest.mark.django_db
def test_jobrequestlist_filter_by_backend_with_broken_pk(rf):
    request = rf.get("/?backend=test")
    request.user = UserFactory()

    with pytest.raises(BadRequest):
        JobRequestList.as_view()(request)


@pytest.mark.django_db
def test_jobrequestlist_filter_by_status(rf):
    JobFactory(job_request=JobRequestFactory(), status="failed")

    JobFactory(job_request=JobRequestFactory(), status="succeeded")

    # Build a RequestFactory instance
    request = rf.get("/?status=succeeded")
    request.user = UserFactory()
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
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_jobrequestlist_filter_by_username(rf):
    user = UserFactory()
    JobRequestFactory(created_by=user)
    JobRequestFactory(created_by=UserFactory())

    # Build a RequestFactory instance
    request = rf.get(f"/?username={user.username}")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_jobrequestlist_filter_by_workspace(rf):
    workspace = WorkspaceFactory()
    JobRequestFactory(workspace=workspace)
    JobRequestFactory()

    # Build a RequestFactory instance
    request = rf.get(f"/?workspace={workspace.pk}")
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_jobrequestlist_filter_by_workspace_with_broken_pk(rf):
    request = rf.get("/?workspace=test")
    request.user = UserFactory()

    with pytest.raises(BadRequest):
        JobRequestList.as_view()(request)


@pytest.mark.django_db
def test_jobrequestlist_find_job_request_by_identifier_form_invalid(rf):
    request = rf.post(MEANINGLESS_URL, {"test-key": "test-value"})
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert response.status_code == 200

    expected = {"identifier": ["This field is required."]}
    assert response.context_data["form"].errors == expected


@pytest.mark.django_db
def test_jobrequestlist_find_job_request_by_identifier_success(rf):
    job_request = JobRequestFactory(identifier="test-identifier")

    request = rf.post(MEANINGLESS_URL, {"identifier": job_request.identifier})
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert response.status_code == 302
    assert response.url == job_request.get_absolute_url()


@pytest.mark.django_db
def test_jobrequestlist_find_job_request_by_identifier_unknown_job_request(rf):
    request = rf.post(MEANINGLESS_URL, {"identifier": "test-value"})
    request.user = UserFactory()
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
    request.user = UserFactory()
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
    request.user = UserFactory()
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
    request.user = UserFactory()
    response = JobRequestList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request

    assert response.context_data["users"] == {user.username: user.name}
    assert len(response.context_data["workspaces"]) == 1


@pytest.mark.django_db
def test_jobrequestlist_with_authenticated_user(rf):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request)

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=False, roles=[])
    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert "Look up JobRequest by Identifier" not in response.rendered_content


@pytest.mark.django_db
def test_jobrequestlist_with_core_developer(rf, core_developer):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request)

    request = rf.get(MEANINGLESS_URL)
    request.user = core_developer
    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert "Look up JobRequest by Identifier" in response.rendered_content


@pytest.mark.django_db
def test_jobrequestlist_with_unauthenticated_user(rf):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request)

    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()
    response = JobRequestList.as_view()(request)
    assert response.status_code == 200
    assert "Look up JobRequest by Identifier" not in response.rendered_content
