import pytest

from interactive.forms import AnalysisRequestForm

from ...fakes import FakeOpenCodelistsAPI


def test_analysisrequestform_success():
    api = FakeOpenCodelistsAPI()
    codelists = api.get_codelists("snomedct") + api.get_codelists("dmd")

    data = {
        "codelist_1_label": "Event Codelist",
        "codelist_1_slug": "bennett/event-codelist/event123",
        "codelist_1_type": "event",
        "codelist_2_label": "Medication Codelist",
        "codelist_2_slug": "bennett/event-codelist/event123",
        "codelist_2_type": "medication",
        "demographics": ["age"],
        "filter_population": "adults",
        "purpose": "For… science!",
        "report_title": "Report on science",
        "time_scale": "months",
        "time_value": "12",
    }
    form = AnalysisRequestForm(data=data, codelists=codelists)

    assert form.is_valid(), form.errors


def test_analysisrequestform_success_without_demogrpahics():
    api = FakeOpenCodelistsAPI()
    codelists = api.get_codelists("snomedct") + api.get_codelists("dmd")

    data = {
        "codelist_1_label": "Event Codelist",
        "codelist_1_slug": "bennett/event-codelist/event123",
        "codelist_1_type": "event",
        "codelist_2_label": "Medication Codelist",
        "codelist_2_slug": "bennett/event-codelist/event123",
        "codelist_2_type": "medication",
        "filter_population": "adults",
        "purpose": "For… science!",
        "report_title": "Report on science",
        "time_scale": "months",
        "time_value": "12",
    }
    form = AnalysisRequestForm(data=data, codelists=codelists)

    assert form.is_valid(), form.errors


@pytest.mark.parametrize(
    "time_scale,time_value", [("weeks", "600"), ("months", "200"), ("years", "17")]
)
def test_analysisrequestform_time_value_validation_failure(time_scale, time_value):
    api = FakeOpenCodelistsAPI()
    codelists = api.get_codelists("snomedct") + api.get_codelists("dmd")

    data = {
        "codelist_1_label": "Event Codelist",
        "codelist_1_slug": "bennett/event-codelist/event123",
        "codelist_1_type": "event",
        "codelist_2_label": "Medication Codelist",
        "codelist_2_slug": "bennett/event-codelist/event123",
        "codelist_2_type": "medication",
        "demographics": ["age"],
        "filter_population": "adults",
        "purpose": "For… science!",
        "report_title": "Report on science",
        "time_scale": time_scale,
        "time_value": time_value,
    }
    form = AnalysisRequestForm(data=data, codelists=codelists)

    assert not form.is_valid(), form.errors


@pytest.mark.parametrize(
    "time_scale,time_value", [("weeks", "200"), ("months", "12"), ("years", "3")]
)
def test_analysisrequestform_time_value_validation_success(time_scale, time_value):
    api = FakeOpenCodelistsAPI()
    codelists = api.get_codelists("snomedct") + api.get_codelists("dmd")

    data = {
        "codelist_1_label": "Event Codelist",
        "codelist_1_slug": "bennett/event-codelist/event123",
        "codelist_1_type": "event",
        "codelist_2_label": "Medication Codelist",
        "codelist_2_slug": "bennett/event-codelist/event123",
        "codelist_2_type": "medication",
        "demographics": ["age"],
        "filter_population": "adults",
        "purpose": "For… science!",
        "report_title": "Report on science",
        "time_scale": time_scale,
        "time_value": time_value,
    }
    form = AnalysisRequestForm(data=data, codelists=codelists)

    assert form.is_valid(), form.errors


def test_analysisrequestform_with_time_ever_and_duration():
    api = FakeOpenCodelistsAPI()
    codelists = api.get_codelists("snomedct") + api.get_codelists("dmd")

    data = {
        "codelist_1_label": "Event Codelist",
        "codelist_1_slug": "bennett/event-codelist/event123",
        "codelist_1_type": "event",
        "codelist_2_label": "Medication Codelist",
        "codelist_2_slug": "bennett/event-codelist/event123",
        "codelist_2_type": "medication",
        "demographics": ["age"],
        "filter_population": "adults",
        "purpose": "For… science!",
        "report_title": "Report on science",
        "time_ever": "yes",
        "time_scale": "weeks",
        "time_value": "52",
    }
    form = AnalysisRequestForm(data=data, codelists=codelists)

    assert not form.is_valid(), form.errors
