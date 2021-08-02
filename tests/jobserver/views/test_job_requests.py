import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import BadRequest
from django.http import Http404
from django.urls import reverse

from jobserver.authorization import ProjectDeveloper
from jobserver.models import Backend, JobRequest
from jobserver.views.job_requests import (
    JobRequestCancel,
    JobRequestDetail,
    JobRequestList,
)

from ...factories import (
    JobFactory,
    JobRequestFactory,
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
    assert response.url == reverse("job-request-detail", kwargs={"pk": job_request.pk})

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
    assert response.url == reverse("job-request-detail", kwargs={"pk": job_request.pk})

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
    assert response.url == reverse("job-request-detail", kwargs={"pk": job_request.pk})

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
def test_jobrequestlist_filters_exist(rf):
    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
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
