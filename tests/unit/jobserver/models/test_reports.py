from ....factories import ReportFactory


def test_report_str():
    report = ReportFactory(title="test")

    assert str(report) == "test"
