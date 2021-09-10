from jobserver.utils import set_from_qs
from staff.views.orgs import OrgDetail, OrgEdit, OrgList

from ....factories import OrgFactory, UserFactory


def test_orgdetail_success(rf, core_developer):
    org = OrgFactory()

    request = rf.get("/")
    request.user = core_developer

    response = OrgDetail.as_view()(request, slug=org.slug)

    assert response.status_code == 200

    expected = set_from_qs(org.members.all())
    output = set_from_qs(response.context_data["members"])
    assert output == expected

    expected = set_from_qs(org.projects.all())
    output = set_from_qs(response.context_data["projects"])
    assert output == expected


def test_orgdetail_unauthorized(rf):
    org = OrgFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = OrgDetail.as_view()(request, slug=org.slug)

    assert response.status_code == 403


def test_orgedit_get_success(rf, core_developer):
    org = OrgFactory()

    request = rf.get("/")
    request.user = core_developer

    response = OrgEdit.as_view()(request, slug=org.slug)

    assert response.status_code == 200


def test_orgedit_get_unauthorized(rf):
    org = OrgFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = OrgEdit.as_view()(request, slug=org.slug)

    assert response.status_code == 403


def test_orgedit_post_success(rf, core_developer):
    org = OrgFactory()

    request = rf.post("/", {"name": "new-name"})
    request.user = core_developer

    response = OrgEdit.as_view()(request, slug=org.slug)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == org.get_staff_url()

    org.refresh_from_db()
    assert org.name == "new-name"


def test_orgedit_post_unauthorized(rf):
    org = OrgFactory()

    request = rf.post("/")
    request.user = UserFactory()

    response = OrgEdit.as_view()(request, slug=org.slug)

    assert response.status_code == 403


def test_orglist_find_by_name(rf, core_developer):
    OrgFactory(name="ben")
    OrgFactory(name="benjamin")
    OrgFactory(name="seb")

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = OrgList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["org_list"]) == 2


def test_orglist_success(rf, core_developer):
    OrgFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = OrgList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["org_list"])


def test_orglist_unauthorized(rf):
    request = rf.post("/")
    request.user = UserFactory()

    response = OrgList.as_view()(request)

    assert response.status_code == 403
