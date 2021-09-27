from django.urls import reverse

from ...factories import ResearcherRegistrationFactory


def test_researcherregistration_get_delete_url():
    researcher = ResearcherRegistrationFactory()

    url = researcher.get_delete_url()

    assert url == reverse(
        "applications:researcher-delete",
        kwargs={"pk": researcher.application.pk, "researcher_pk": researcher.pk},
    )


def test_researcherregistration_get_edit_url():
    researcher = ResearcherRegistrationFactory()

    url = researcher.get_edit_url()

    assert url == reverse(
        "applications:researcher-edit",
        kwargs={"pk": researcher.application.pk, "researcher_pk": researcher.pk},
    )


def test_researcherregistration_str():
    researcher = ResearcherRegistrationFactory()

    assert str(researcher) == researcher.name
