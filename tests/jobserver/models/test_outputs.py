import pytest
from django.conf import settings
from django.urls import reverse

from tests.factories import ReleaseFactory


@pytest.mark.django_db
def test_release_get_absolute_url():
    release = ReleaseFactory()

    url = release.get_absolute_url()
    assert url == reverse(
        "workspace-release",
        kwargs={
            "org_slug": release.workspace.project.org.slug,
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "release": release.id,
        },
    )


@pytest.mark.django_db
def test_release_file_path():
    files = {"file.txt": "test_release_creation"}
    release = ReleaseFactory(files=files)

    assert release.file_path("notextists") is None

    expected = (
        settings.RELEASE_STORAGE / f"{release.workspace.name}/{release.id}/file.txt"
    )
    path = release.file_path("file.txt")
    assert path == expected
    assert path.read_text() == "test_release_creation"

    path.unlink()
    assert release.file_path("file.txt") is None
