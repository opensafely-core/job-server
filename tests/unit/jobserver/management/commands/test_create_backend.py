from django.core.management import call_command

from jobserver.models import Backend, User
from tests.factories.user import UserFactory


def test_create_backend(capsys):
    call_command("create_backend", "testslug", "--quiet")

    token = capsys.readouterr().out.strip()
    backend = Backend.objects.get(slug="testslug")
    assert backend.slug == "testslug"
    assert backend.name == "testslug"
    assert backend.level_4_url == ""
    assert backend.auth_token == token

    # calling again doesn't create new backend, but does update metadata
    call_command(
        "create_backend", "testslug", "--name=testname", "--url=url", "--quiet"
    )
    backend = Backend.objects.get(slug="testslug")
    assert backend.slug == "testslug"
    assert backend.name == "testname"
    assert backend.level_4_url == "url"
    assert backend.auth_token == token  # same token


def test_create_backend_user():
    user = UserFactory()
    user.save()
    call_command(
        "create_backend",
        "testslug",
        f"--user={user.username}",
    )
    backend = Backend.objects.get(slug="testslug")
    # refresh user
    user = User.objects.get(username=user.username)
    assert backend in user.backends.all()

    call_command(
        "create_backend",
        "testslug",
        f"--user={user.username}",
    )
