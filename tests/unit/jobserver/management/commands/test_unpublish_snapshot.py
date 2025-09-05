import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from tests.factories import PublishRequestFactory, SnapshotFactory, UserFactory


def test_command_no_snapshot():
    with pytest.raises(CommandError, match="Snapshot '1' does not exist"):
        call_command("unpublish_snapshot", 1, "a-username")


def test_command_no_user():
    snapshot = SnapshotFactory()
    with pytest.raises(CommandError, match="User 'a-username' does not exist"):
        call_command("unpublish_snapshot", snapshot.pk, "a-username")


def test_command_snapshot_not_published():
    snapshot = SnapshotFactory()
    user = UserFactory()
    with pytest.raises(CommandError, match=r"Snapshot '\d+' is not published"):
        call_command("unpublish_snapshot", snapshot.pk, user.username)


def test_command(capsys):
    # We explicitly create different users to approve (publish) and retrospectively
    # reject (unpublish) the request. These users are not the user who created
    # the request. The user who created the request is created implicitly by
    # the factory. We do this to demonstrate that *any user* can retrospectively reject
    # the request.
    publish_request = PublishRequestFactory()
    publish_request.approve(user=UserFactory())
    rejector = UserFactory()

    call_command("unpublish_snapshot", publish_request.snapshot.pk, rejector.username)

    assert not publish_request.snapshot.is_published
    out, _ = capsys.readouterr()
    out_line_1, out_line_2 = out.splitlines()
    assert out_line_1.startswith(f"User '{rejector.username}' is about to reject")
    assert out_line_2.startswith(f"User '{rejector.username}' has rejected")
