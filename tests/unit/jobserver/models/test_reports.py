import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Report

from ....factories import ReportFactory, UserFactory


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_report_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReportFactory(**{field: None})


def test_report_get_staff_url():
    report = ReportFactory()

    url = report.get_staff_url()

    assert url == reverse("staff:report-detail", kwargs={"pk": report.pk})


def test_report_str():
    report = ReportFactory(title="test")

    assert str(report) == "test"


def test_report_published_check_constraint_missing_at():
    with pytest.raises(IntegrityError):
        ReportFactory(published_at=None, published_by=UserFactory())


def test_report_published_check_constraint_missing_by():
    with pytest.raises(IntegrityError):
        # published_at uses auto_now so any value we passed in here is ignored
        ReportFactory(published_at=timezone.now(), published_by=None)


def test_report_updated_check_constraint_missing_at():
    ReportFactory(updated_by=UserFactory())

    with pytest.raises(IntegrityError):
        # use update here because auto_now doesn't apply to this type of query
        Report.objects.update(updated_at=None)


def test_report_updated_check_constraint_missing_by():
    with pytest.raises(IntegrityError):
        # updated_at uses auto_now so any value we passed in here is ignored
        ReportFactory(updated_by=None)
