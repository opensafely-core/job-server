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
def test_release_manifest():
    files = {"file.txt": "test_release_creation"}
    release = ReleaseFactory(files=files)

    assert release.manifest == {"workspace": "workspace", "repo": "repo"}


@pytest.mark.django_db
def test_release_file_absolute_path():
    files = {"file.txt": "test_absolute_path"}
    release = ReleaseFactory(files=files)
    rfile = release.files.get(name="file.txt")

    expected = (
        settings.RELEASE_STORAGE
        / f"{release.workspace.name}/releases/{release.id}/file.txt"
    )
    path = rfile.absolute_path()
    assert path == expected
    assert path.read_text() == "test_absolute_path"
