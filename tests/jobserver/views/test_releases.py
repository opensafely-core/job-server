import pytest
from django.http import Http404

from jobserver.views.releases import Releases

from ...factories import OrgFactory, ProjectFactory


@pytest.mark.django_db
def test_releases_success(rf):
    project = ProjectFactory()

    request = rf.get("/")

    response = Releases.as_view()(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_releases_unknown_project(rf):
    org = OrgFactory()

    request = rf.get("/")
    with pytest.raises(Http404):
        Releases.as_view()(request, org_slug=org.slug, project_slug="")
