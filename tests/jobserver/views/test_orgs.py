import pytest
from django.http import Http404

from jobserver.models import Org
from jobserver.views.orgs import OrgCreate, OrgDetail, OrgList

from ...factories import OrgFactory


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_orgcreate_get_success(rf, superuser):
    oxford = OrgFactory(name="University of Oxford")
    ebmdatalab = OrgFactory(name="EBMDataLab")

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = OrgCreate.as_view()(request)

    assert response.status_code == 200

    orgs = response.context_data["orgs"]
    assert len(orgs) == 3
    assert orgs[1] == ebmdatalab
    assert orgs[2] == oxford


@pytest.mark.django_db
def test_orgcreate_post_success(rf, superuser):
    request = rf.post(MEANINGLESS_URL, {"name": "A New Org"})
    request.user = superuser
    response = OrgCreate.as_view()(request)

    assert response.status_code == 302

    orgs = Org.objects.all()
    assert len(orgs) == 2

    org = orgs[1]
    assert org.name == "A New Org"
    assert response.url == org.get_absolute_url()


@pytest.mark.django_db
def test_orgdetail_success(rf, superuser):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = OrgDetail.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200


@pytest.mark.django_db
def test_orgdetail_unknown_org(rf, superuser):
    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        OrgDetail.as_view()(request, org_slug="")


@pytest.mark.django_db
def test_orglist_success(rf, superuser):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = OrgList.as_view()(request)

    assert response.status_code == 200
    assert org in response.context_data["object_list"]
