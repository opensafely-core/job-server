import pytest
from django.http import Http404

from jobserver.models import Org
from jobserver.views.orgs import OrgCreate, OrgDetail, OrgList

from ....factories import (
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    UserFactory,
    WorkspaceFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_orgcreate_get_success(rf, core_developer):
    oxford = OrgFactory(name="University of Oxford")
    ebmdatalab = OrgFactory(name="EBMDataLab")

    request = rf.get(MEANINGLESS_URL)
    request.user = core_developer
    response = OrgCreate.as_view()(request)

    assert response.status_code == 200

    orgs = response.context_data["orgs"]
    assert len(orgs) == 3
    assert orgs[1] == ebmdatalab
    assert orgs[2] == oxford


@pytest.mark.django_db
def test_orgcreate_post_success(rf, core_developer):
    request = rf.post(MEANINGLESS_URL, {"name": "A New Org"})
    request.user = core_developer
    response = OrgCreate.as_view()(request)

    assert response.status_code == 302

    orgs = Org.objects.all()
    assert len(orgs) == 2

    org = orgs[1]
    assert org.name == "A New Org"
    assert response.url == org.get_absolute_url()


@pytest.mark.django_db
def test_orgdetail_success(rf):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = OrgDetail.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200


@pytest.mark.django_db
def test_orgdetail_unknown_org(rf):
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    with pytest.raises(Http404):
        OrgDetail.as_view()(request, org_slug="")


@pytest.mark.django_db
def test_orgdetail_unknown_org_but_known_workspace(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    response = OrgDetail.as_view()(request, org_slug=workspace.name)

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()


@pytest.mark.django_db
def test_orgdetail_with_org_member(rf):
    org = OrgFactory()
    user = UserFactory()
    OrgMembershipFactory(org=org, user=user)

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = OrgDetail.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200
    assert "Register Project" in response.rendered_content


@pytest.mark.django_db
def test_orgdetail_with_non_member_user(rf):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = OrgDetail.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200
    assert "Register Project" not in response.rendered_content


@pytest.mark.django_db
def test_orglist_success(rf):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    response = OrgList.as_view()(request)

    assert response.status_code == 200
    assert org in response.context_data["object_list"]
