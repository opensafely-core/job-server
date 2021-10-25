import pytest
from django import forms

from applications.forms import (
    ResearcherRegistrationSubmissionForm,
    YesNoField,
    coerce_to_bool,
)


def test_coerce_with_booleans():
    assert coerce_to_bool(True)
    assert not coerce_to_bool(False)


def test_coerce_with_expected_strings():
    assert coerce_to_bool("true")
    assert coerce_to_bool("True")
    assert not coerce_to_bool("false")
    assert not coerce_to_bool("False")


def test_coerce_with_incorrect_type():
    msg = '^"3" was of type int, expected bool or string$'
    with pytest.raises(TypeError, match=msg):
        coerce_to_bool(3)


def test_coerce_with_unexpected_string():
    msg = (
        '^Expected string value to be one of: true, True, false, or False, got "test"$'
    )
    with pytest.raises(ValueError, match=msg):
        coerce_to_bool("test")


def test_required_fields():
    data = {
        "name": "ben",
        "job_title": "The Boss",
        "email": "ben@example.com",
        "does_researcher_need_server_access": None,
        "has_taken_safe_researcher_training": None,
    }
    form = ResearcherRegistrationSubmissionForm(data)
    assert not form.is_valid()
    assert "does_researcher_need_server_access" in form.errors
    assert "has_taken_safe_researcher_training" in form.errors

    data = {
        "name": "ben",
        "job_title": "The Boss",
        "email": "ben@example.com",
        "does_researcher_need_server_access": False,
        "has_taken_safe_researcher_training": False,
    }
    form = ResearcherRegistrationSubmissionForm(data)
    assert form.is_valid(), form.errors


def test_researcherregistrationsubmissionform_does_researcher_need_server_access_related_validation():
    data = {
        "name": "ben",
        "job_title": "The Boss",
        "email": "ben@example.com",
        "does_researcher_need_server_access": True,
        "has_taken_safe_researcher_training": False,
    }
    form = ResearcherRegistrationSubmissionForm(data)
    assert not form.is_valid()

    assert "telephone" in form.errors
    assert "phone_type" in form.errors

    data = {
        "name": "ben",
        "job_title": "The Boss",
        "email": "ben@example.com",
        "does_researcher_need_server_access": True,
        "telephone": "07777777777",
        "phone_type": "iphone",
        "has_taken_safe_researcher_training": False,
    }
    form = ResearcherRegistrationSubmissionForm(data)
    assert form.is_valid()


def test_researcherregistrationsubmissionform_has_taken_safe_reseasrcher_training_validation():
    data = {
        "name": "ben",
        "job_title": "The Boss",
        "email": "ben@example.com",
        "does_researcher_need_server_access": False,
        "has_taken_safe_researcher_training": True,
    }
    form = ResearcherRegistrationSubmissionForm(data)
    assert not form.is_valid()

    assert "training_with_org" in form.errors
    assert "training_passed_at" in form.errors

    data = {
        "name": "ben",
        "job_title": "The Boss",
        "email": "ben@example.com",
        "does_researcher_need_server_access": False,
        "has_taken_safe_researcher_training": True,
        "training_with_org": "Oxford",
        "training_passed_at": "2021-06-01",
    }
    form = ResearcherRegistrationSubmissionForm(data)
    assert form.is_valid()


def test_yesnofield_coerce():
    class Form(forms.Form):
        yes_no_field = YesNoField()

    # "True" coerces to True
    form = Form({"yes_no_field": "True"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["yes_no_field"]

    # "False" coerces to False
    form = Form({"yes_no_field": "False"})
    assert form.is_valid(), form.errors
    assert not form.cleaned_data["yes_no_field"]
