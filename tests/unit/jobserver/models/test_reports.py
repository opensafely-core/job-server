from django.urls import reverse

from ....factories import ReportFactory


def test_report_get_staff_url():
    report = ReportFactory()

    url = report.get_staff_url()

    assert url == reverse("staff:report-detail", kwargs={"pk": report.pk})


def test_report_str():
    report = ReportFactory(title="test")

    assert str(report) == "test"
