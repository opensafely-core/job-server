import pytest
from django.contrib.auth.models import AnonymousUser

from jobserver.views.index import Index

from ...factories import (
    JobRequestFactory,
    OrgFactory,
    OrgMembershipFactory,
    UserFactory,
    WorkspaceFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_index_success(rf, mocker, user):
    workspace = WorkspaceFactory()
    JobRequestFactory.create_batch(10, workspace=workspace)

    # mock GitHub Org membership
    mocker.patch("jobserver.views.index.can_run_jobs", autospec=True, return_value=True)

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = Index.as_view()(request)

    assert len(response.context_data["job_requests"]) == 5
    assert len(response.context_data["workspaces"]) == 1


@pytest.mark.django_db
def test_index_with_authenticated_user_in_multiple_orgs(rf, mocker, user):
    """Check the Add Workspace button is rendered for authenticated Users in multiple Orgs."""
    WorkspaceFactory()

    # set up a second Org & tie the User to it
    OrgMembershipFactory(org=OrgFactory(), user=user)

    # mock GitHub Org membership
    mocker.patch("jobserver.views.index.can_run_jobs", autospec=True, return_value=True)

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = Index.as_view()(request)

    assert "Pick an organisation" in response.rendered_content
    assert "Add a New Workspace" in response.rendered_content


@pytest.mark.django_db
def test_index_with_authenticated_user_in_one_org(rf, mocker, user):
    """Check the Add Workspace button is rendered for authenticated Users in a single Org."""
    WorkspaceFactory()

    # mock GitHub Org membership
    mocker.patch("jobserver.views.index.can_run_jobs", autospec=True, return_value=True)

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = Index.as_view()(request)

    assert "Pick a project" in response.rendered_content
    assert "Add a New Workspace" in response.rendered_content


@pytest.mark.django_db
def test_index_with_authenticated_but_partially_registered_user(rf, mocker):
    """
    Check the Add Workspace button is rendered for authenticated Users on the
    homepage.
    """
    # mock a lack of GitHub Org membership
    mocker.patch(
        "jobserver.views.index.can_run_jobs", autospec=True, return_value=False
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    response = Index.as_view()(request)

    assert "Add a New Workspace" not in response.rendered_content


@pytest.mark.django_db
def test_index_with_unauthenticated_user(rf):
    """
    Check the Add Workspace button is not rendered for unauthenticated Users on
    the homepage.
    """
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()

    response = Index.as_view()(request)

    assert "Add a New Workspace" not in response.rendered_content
