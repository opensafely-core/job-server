import pytest
from django.http import Http404

from jobserver.views.orgs import OrgDetail, OrgList

from ....factories import (
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_orgdetail_success(rf):
    org = OrgFactory()

    request = rf.get("/")
    request.user = UserFactory()
    response = OrgDetail.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200


def test_orgdetail_unknown_org(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        OrgDetail.as_view()(request, org_slug="")


def test_orgdetail_unknown_org_but_known_workspace(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    request = rf.get("/")
    request.user = UserFactory()

    response = OrgDetail.as_view()(request, org_slug=workspace.name)

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()


def test_orgdetail_with_org_member(rf):
    org = OrgFactory()
    user = UserFactory()
    OrgMembershipFactory(org=org, user=user)

    request = rf.get("/")
    request.user = user

    response = OrgDetail.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200
    assert "Register Project" in response.rendered_content


def test_orgdetail_with_non_member_user(rf):
    org = OrgFactory()

    request = rf.get("/")
    request.user = UserFactory()
    response = OrgDetail.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200
    assert "Register Project" not in response.rendered_content


def test_orglist_success(rf):
    org = OrgFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = OrgList.as_view()(request)

    assert response.status_code == 200
    assert org in response.context_data["object_list"]
