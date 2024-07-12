import pytest
from django.core import mail

from airlock.emails import (
    send_request_rejected_email,
    send_request_released_email,
    send_request_returned_email,
)
from airlock.views import AirlockEvent, EventType
from tests.factories import (
    BackendFactory,
    BackendMembershipFactory,
    ReleaseFactory,
    UserFactory,
    WorkspaceFactory,
)


@pytest.fixture
def airlock_event():
    def _airlock_event(event_type, updates):
        author = UserFactory(username="author", email="author@example.com")

        workspace = WorkspaceFactory(name="test-workspace")
        backend = BackendFactory(auth_token="test", name="test-backend")
        BackendMembershipFactory(backend=backend, user=author)

        return AirlockEvent(
            event_type=event_type,
            workspace=workspace,
            updates=updates,
            release_request_id="request-id",
            request_author=author,
            user=author,
            org="org",
            repo="repo",
        )

    yield _airlock_event


@pytest.mark.parametrize(
    "updates,expected_email_updates",
    [
        ([], []),
        (
            [
                {"update": "change requested"},
                {"update": "file rejected", "user": "test"},
            ],
            ["change requested", "file rejected by user test"],
        ),
    ],
)
def test_returned_email(airlock_event, updates, expected_email_updates):
    event = airlock_event(EventType.REQUEST_RETURNED, updates=updates)
    send_request_returned_email(event)
    assert_email(event, "Release request returned", expected_email_updates)


@pytest.mark.parametrize(
    "updates,expected_email_updates",
    [
        ([], []),
        ([{"update": "comment added", "user": "test"}], ["comment added by user test"]),
    ],
)
def test_rejected_email(airlock_event, updates, expected_email_updates):
    event = airlock_event(EventType.REQUEST_REJECTED, updates=updates)
    send_request_rejected_email(event)
    assert_email(event, "Release request rejected", expected_email_updates)


@pytest.mark.parametrize(
    "updates,expected_email_updates",
    [
        ([], []),
        ([{"update": "comment added", "user": "test"}], ["comment added by user test"]),
    ],
)
def test_released_email(airlock_event, updates, expected_email_updates):
    ReleaseFactory(id="request-id")
    event = airlock_event(EventType.REQUEST_RELEASED, updates=updates)
    send_request_released_email(event)
    assert_email(event, "Files released", expected_email_updates)


def assert_email(airlock_event, subject, expected_email_updates):
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == ["author@example.com"]
    assert subject in email.subject

    update_strings = airlock_event.describe_updates()
    assert update_strings[0] not in email.body
    assert update_strings[1:] == expected_email_updates
    for update in expected_email_updates:
        assert update in email.body
