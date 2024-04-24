from unittest.mock import patch

import pytest
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

    def create_issue_comment(*args, **kwargs):
        raise HTTPError()

    def close_issue(*args, **kwargs):
        raise HTTPError()


@pytest.mark.parametrize(
    "event_type,group,update_type",
    [
        ("request_submitted", None, None),
        ("request_rejected", None, None),
        ("request_withdrawn", None, None),
        ("request_released", None, None),
        ("request_updated", "Group 1", "file_added"),
        ("request_updated", "Group 1", "file_withdrawn"),
        ("request_updated", "Group 1", "context_edited"),
        ("request_updated", "Group 1", "controls_edited"),
        ("request_updated", "Group 1", "comment_added"),
    ],
)
@patch("airlock.views._get_github_api", FakeGitHubAPI)
def test_api_airlock_event_post(api_rf, event_type, group, update_type):
    user = UserFactory()
    WorkspaceFactory(name="test-workspace")
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)

    data = {
        "event_type": event_type,
        "update_type": update_type,
        "group": group,
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


@pytest.mark.parametrize(
    "event_type,update_type,group,error",
    [
        ("request_submitted", None, None, "Error creating GitHub issue"),
        ("request_rejected", None, None, "Error closing GitHub issue"),
        (
            "request_updated",
            "file_added",
            "Group 1",
            "Error creating GitHub issue comment",
        ),
    ],
)
@patch("airlock.views._get_github_api", FakeGithubApiWithError)
def test_api_airlock_event_error(api_rf, event_type, update_type, group, error):

    author = UserFactory()
    user = UserFactory()
    WorkspaceFactory(name="test-workspace")
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)

    data = {
        "event_type": event_type,
        "update_type": update_type,
        "group": group,
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
        "message": error,
    }
