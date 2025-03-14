import pytest
from django.db import IntegrityError

from interactive.models import AnalysisRequest

from ...factories import (
    AnalysisRequestFactory,
    UserFactory,
)


def test_analysisrequest_constraints_updated_at_and_updated_by_both_set():
    AnalysisRequestFactory(updated_by=UserFactory())


@pytest.mark.django_db(transaction=True)
def test_analysisrequest_constraints_missing_updated_at_or_updated_by():
    with pytest.raises(IntegrityError):
        AnalysisRequestFactory(updated_by=None)

    with pytest.raises(IntegrityError):
        ar = AnalysisRequestFactory(updated_by=UserFactory())

        # use update to work around auto_now always firing on save()
        AnalysisRequest.objects.filter(pk=ar.pk).update(updated_at=None)


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_analysisrequest_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        AnalysisRequestFactory(**{field: None})


def test_analysisrequest_str():
    analysis_request = AnalysisRequestFactory()

    assert str(analysis_request) == analysis_request.title


def test_analysisrequest_visible_to_creator():
    analysis_request = AnalysisRequestFactory()

    assert analysis_request.visible_to(analysis_request.created_by)


def test_analysisrequest_visible_to_staff(staff_area_administrator):
    analysis_request = AnalysisRequestFactory()

    assert analysis_request.visible_to(staff_area_administrator)


def test_analysisrequest_visible_to_other_user():
    analysis_request = AnalysisRequestFactory()

    assert not analysis_request.visible_to(UserFactory())


def test_analysisrequest_ulid():
    assert AnalysisRequestFactory().ulid.timestamp
