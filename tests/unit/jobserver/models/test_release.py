import pytest
from django.db import IntegrityError
from django.urls import reverse

from tests.factories import ReleaseFactory


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_release_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReleaseFactory(**{field: None})


def test_release_get_absolute_url():
    release = ReleaseFactory()

    url = release.get_absolute_url()

    assert url == reverse(
        "release-detail",
        kwargs={
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "pk": release.id,
        },
    )


def test_release_get_api_url():
    release = ReleaseFactory()

    assert release.get_api_url() == f"/api/v2/releases/release/{release.id}"


def test_release_get_download_url():
    release = ReleaseFactory()

    url = release.get_download_url()

    assert url == reverse(
        "release-download",
        kwargs={
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "pk": release.id,
        },
    )


def test_release_ulid():
    assert ReleaseFactory().ulid.timestamp
