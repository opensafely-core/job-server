from django.urls import reverse

from ....factories import OrgFactory


def test_org_default_for_github_orgs():
    org1 = OrgFactory()
    assert org1.github_orgs == ["opensafely"]

    org2 = OrgFactory()
    assert org2.github_orgs == ["opensafely"]

    # does mutating the field affect the other object?
    org1.github_orgs += ["test"]
    org1.save()
    org1.refresh_from_db()

    assert org1.github_orgs == ["opensafely", "test"]
    assert org2.github_orgs == ["opensafely"]


def test_org_get_absolute_url():
    org = OrgFactory()
    url = org.get_absolute_url()
    assert url == reverse("org-detail", kwargs={"slug": org.slug})


def test_org_get_edit_url():
    org = OrgFactory()

    url = org.get_edit_url()

    assert url == reverse("staff:org-edit", kwargs={"slug": org.slug})


def test_org_get_logs_url():
    org = OrgFactory()

    url = org.get_logs_url()

    assert url == reverse("org-event-log", kwargs={"slug": org.slug})


def test_org_get_staff_url():
    org = OrgFactory()

    url = org.get_staff_url()

    assert url == reverse("staff:org-detail", kwargs={"slug": org.slug})


def test_org_populates_slug():
    assert OrgFactory(name="Test Org", slug="").slug == "test-org"


def test_org_str():
    assert str(OrgFactory(name="Test Org")) == "Test Org"
