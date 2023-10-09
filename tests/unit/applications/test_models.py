import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from ...factories import ApplicationFactory, ResearcherRegistrationFactory, UserFactory


def test_application_constraints_approved_at_and_approved_by_both_set():
    ApplicationFactory(approved_at=timezone.now(), approved_by=UserFactory())


def test_application_constraints_approved_at_and_approved_by_neither_set():
    ApplicationFactory(approved_at=None, approved_by=None)


def test_application_constraints_deleted_at_and_deleted_by_both_set():
    ApplicationFactory(deleted_at=timezone.now(), deleted_by=UserFactory())


def test_application_constraints_deleted_at_and_deleted_by_neither_set():
    ApplicationFactory(deleted_at=None, deleted_by=None)


@pytest.mark.django_db(transaction=True)
def test_application_constraints_missing_approved_at_or_approved_by():
    msg = '^new row for relation "applications_application" violates check constraint "applications_application_both_approved_at_and_approved_by_set"'

    with pytest.raises(IntegrityError, match=msg):
        ApplicationFactory(approved_at=timezone.now(), approved_by=None)

    with pytest.raises(IntegrityError, match=msg):
        ApplicationFactory(approved_at=None, approved_by=UserFactory())


@pytest.mark.django_db(transaction=True)
def test_application_constraints_missing_deleted_at_or_deleted_by():
    with pytest.raises(IntegrityError):
        ApplicationFactory(deleted_at=timezone.now(), deleted_by=None)

    with pytest.raises(IntegrityError):
        ApplicationFactory(deleted_at=None, deleted_by=UserFactory())


def test_application_get_absolute_url():
    application = ApplicationFactory()

    url = application.get_absolute_url()

    assert url == reverse(
        "applications:detail", kwargs={"pk_hash": application.pk_hash}
    )


def test_application_get_edit_url():
    application = ApplicationFactory()

    url = application.get_edit_url()

    assert url == reverse(
        "staff:application-edit", kwargs={"pk_hash": application.pk_hash}
    )


def test_application_get_delete_url():
    application = ApplicationFactory()

    url = application.get_delete_url()

    assert url == reverse(
        "applications:delete", kwargs={"pk_hash": application.pk_hash}
    )


def test_application_get_restore_url():
    application = ApplicationFactory()

    url = application.get_restore_url()

    assert url == reverse(
        "applications:restore", kwargs={"pk_hash": application.pk_hash}
    )


def test_application_get_staff_delete_url():
    application = ApplicationFactory()

    url = application.get_staff_delete_url()

    assert url == reverse(
        "staff:application-delete", kwargs={"pk_hash": application.pk_hash}
    )


def test_application_get_staff_restore_url():
    application = ApplicationFactory()

    url = application.get_staff_restore_url()

    assert url == reverse(
        "staff:application-restore", kwargs={"pk_hash": application.pk_hash}
    )


def test_application_get_staff_url():
    application = ApplicationFactory()

    url = application.get_staff_url()

    assert url == reverse(
        "staff:application-detail", kwargs={"pk_hash": application.pk_hash}
    )


def test_application_is_deleted():
    assert not ApplicationFactory().is_deleted

    application = ApplicationFactory(
        deleted_at=timezone.now(), deleted_by=UserFactory()
    )
    assert application.is_deleted


def test_application_str():
    user = UserFactory(fullname="Ben Goldacre")
    application = ApplicationFactory(created_by=user)

    assert str(application) == f"Application {application.pk_hash} by Ben Goldacre"


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

    assert url == reverse(
        "staff:researcher-edit",
        kwargs={
            "pk_hash": researcher.application.pk_hash,
            "pk": researcher.pk,
        },
    )


def test_researcherregistration_str():
    researcher = ResearcherRegistrationFactory()

    assert str(researcher) == researcher.name
