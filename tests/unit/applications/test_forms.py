from django import forms

from applications.forms import ResearcherRegistrationSubmissionForm, YesNoField


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
