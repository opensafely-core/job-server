import pytest
from django.urls import reverse

from ...factories import OrgFactory, ProjectFactory, ReleaseFactory, WorkspaceFactory


@pytest.mark.django_db
def test_release_creation():
    release = ReleaseFactory(files=["file.txt"], upload_dir="workspace/release")

    assert str(release.file_path("file.txt")) == "releases/workspace/release/file.txt"


@pytest.mark.django_db
def test_release_get_absolute_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)
    release = ReleaseFactory(workspace=workspace)

    url = release.get_absolute_url()

    assert url == reverse(
        "workspace-release",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "workspace_slug": workspace.name,
            "release": release.id,
        },
    )
