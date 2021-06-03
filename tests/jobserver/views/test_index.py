import pytest
from django.contrib.auth.models import AnonymousUser

from jobserver.views.index import Index

from ...factories import JobRequestFactory, UserFactory, WorkspaceFactory


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_index_success(rf, mocker):
    JobRequestFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    mocker.patch("jobserver.views.index.can_run_jobs", return_value=True, autospec=True)
    response = Index.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["job_requests"]) == 1
    assert len(response.context_data["workspaces"]) == 1


@pytest.mark.django_db
def test_index_with_authenticated_user(rf, mocker):
    """
    Check the Add Workspace button is rendered for authenticated Users on the
    homepage.
    """
    JobRequestFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    mocker.patch("jobserver.views.index.can_run_jobs", return_value=True, autospec=True)
    response = Index.as_view()(request)

    assert "Add a New Workspace" in response.rendered_content


@pytest.mark.django_db
def test_index_with_authenticated_but_partially_registered_user(rf, mocker):
    """
    Check the Add Workspace button is rendered for authenticated Users on the
    homepage.
    """
    JobRequestFactory(workspace=WorkspaceFactory())

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    mocker.patch(
        "jobserver.views.index.can_run_jobs", return_value=False, autospec=True
    )
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
