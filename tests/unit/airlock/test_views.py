from unittest.mock import patch

from requests.exceptions import HTTPError

from airlock.views import airlock_event_view
from tests.factories import (
    BackendFactory,
    BackendMembershipFactory,
    UserFactory,
    WorkspaceFactory,
)
from tests.fakes import FakeGitHubAPI


class FakeGithubApiWithError:
    def create_issue(*args, **kwargs):
        raise HTTPError()


@patch("airlock.views._get_github_api", FakeGitHubAPI)
def test_api_post_release_request_submitted(api_rf):
    user = UserFactory()
    WorkspaceFactory(name="test-workspace")
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)

    data = {
        "event_type": "request_submitted",
        "update_type": None,
        "workspace": "test-workspace",
        "request": "01AAA1AAAAAAA1AAAAA11A1AAA",
        "request_author": user.username,
        "user": user.username,
    }
    request = api_rf.post(
        "/",
        data=data,
        format="json",
        headers={
            "authorization": "test",
            "os-user": user.username,
        },
    )
    response = airlock_event_view(request)
    assert response.status_code == 201
    assert response.data == {"status": "ok"}


@patch("airlock.views._get_github_api", FakeGitHubAPI)
def test_api_post_release_request_submitted_by_non_author(api_rf):
    author = UserFactory()
    user = UserFactory()
    WorkspaceFactory(name="test-workspace")
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)

    data = {
        "event_type": "request_submitted",
        "update_type": None,
        "workspace": "test-workspace",
        "request": "01AAA1AAAAAAA1AAAAA11A1AAA",
        "request_author": author.username,
        "user": user.username,
    }
    request = api_rf.post(
        "/",
        data=data,
        format="json",
        headers={
            "authorization": "test",
            "os-user": user.username,
        },
    )
    response = airlock_event_view(request)
    assert response.status_code == 201
    assert response.data == {"status": "ok"}


@patch("airlock.views._get_github_api", FakeGithubApiWithError)
def test_api_post_post_release_request_submitted_error(api_rf):

    author = UserFactory()
    user = UserFactory()
    WorkspaceFactory(name="test-workspace")
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)

    data = {
        "event_type": "request_submitted",
        "update_type": None,
        "workspace": "test-workspace",
        "request": "01AAA1AAAAAAA1AAAAA11A1AAA",
        "request_author": author.username,
        "user": user.username,
    }
    request = api_rf.post(
        "/",
        data=data,
        format="json",
        headers={
            "authorization": "test",
            "os-user": user.username,
        },
    )
    response = airlock_event_view(request)
    assert response.status_code == 201
    assert response.data == {
        "status": "error",
        "message": "Error creating GitHub issue",
    }
