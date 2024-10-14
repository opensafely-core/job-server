from django.core.management import call_command

from jobserver.authorization.roles import (
    OutputChecker,
    StaffAreaAdministrator,
)
from jobserver.models import User


def test_create_user_defaults(capsys):
    call_command("create_user", "username")

    user = User.objects.get(username="username")

    assert user.email == "username@example.com"
    assert user.fullname == "username"
    assert user.roles == []

    # test idempotency
    call_command("create_user", "username")


def test_create_user_args(capsys):
    call_command(
        "create_user",
        "username",
        "--email=foo@bar.com",
        "--name=fullname",
        "--staff-area-administrator",
        "--output-checker",
    )

    user = User.objects.get(username="username")

    assert user.email == "foo@bar.com"
    assert user.fullname == "fullname"
    assert set(user.roles) == set([OutputChecker, StaffAreaAdministrator])

    # test idempotency
    call_command(
        "create_user",
        "username",
        "--email=foo@bar.com",
        "--name=fullname",
        "--output-checker",
        "--staff-area-administrator",
    )
