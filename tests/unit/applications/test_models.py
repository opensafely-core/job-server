import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from ...factories import ApplicationFactory, ResearcherRegistrationFactory, UserFactory


def test_application_constraint_approved_at_and_approved_by_both_set():
    ApplicationFactory(approved_at=timezone.now(), approved_by=UserFactory())


@pytest.mark.django_db(transaction=True)
def test_application_constraint_missing_approved_at_or_approved_by():
    msg = '^new row for relation "applications_application" violates check constraint "applications_application_both_approved_at_and_approved_by_set"'

    with pytest.raises(IntegrityError, match=msg):
        ApplicationFactory(approved_at=timezone.now(), approved_by=None)

    with pytest.raises(IntegrityError, match=msg):
        ApplicationFactory(approved_at=None, approved_by=UserFactory())


def test_application_get_absolute_url():
    application = ApplicationFactory()

    url = application.get_absolute_url()

    return url == reverse(
        "applications:detail", kwargs={"pk_hash": application.pk_hash}
    )


def test_application_get_staff_url():
    application = ApplicationFactory()

    url = application.get_staff_url()

    return url == reverse(
        "staff:application-detail", kwargs={"pk_hash": application.pk_hash}
    )


def test_application_str():
    user = UserFactory(first_name="Ben", last_name="Seb")
    application = ApplicationFactory(created_by=user)

    assert str(application) == f"Application {application.pk_hash} by Ben Seb"


def test_researcherregistration_get_absolute_url():
    researcher = ResearcherRegistrationFactory()

    url = researcher.get_absolute_url()

    assert url == reverse(
        "applications:researcher-detail",
        kwargs={
            "pk_hash": researcher.application.pk_hash,
            "researcher_pk": researcher.pk,
        },
    )


def test_researcherregistration_get_delete_url():
    researcher = ResearcherRegistrationFactory()

    url = researcher.get_delete_url()

    assert url == reverse(
        "applications:researcher-delete",
        kwargs={
            "pk_hash": researcher.application.pk_hash,
            "researcher_pk": researcher.pk,
        },
    )


def test_researcherregistration_get_edit_url():
    researcher = ResearcherRegistrationFactory()

    url = researcher.get_edit_url()

    assert url == reverse(
        "applications:researcher-edit",
        kwargs={
            "pk_hash": researcher.application.pk_hash,
            "researcher_pk": researcher.pk,
        },
    )


def test_researcherregistration_get_staff_edit_url():
    researcher = ResearcherRegistrationFactory()

    url = researcher.get_staff_edit_url()

    assert url == reverse("staff:researcher-edit", kwargs={"pk": researcher.pk})


def test_researcherregistration_str():
    researcher = ResearcherRegistrationFactory()

    assert str(researcher) == researcher.name
