from applications.forms import ResearcherRegistrationForm


def test_researcherregistrationform_completely_filled_in():
    form = ResearcherRegistrationForm(
        {
            "name": "test",
            "job_title": "test",
            "email": "test",
            "does_researcher_need_server_access": True,
            "telephone": "test",
            "phone_type": "iphone",
            "has_taken_safe_researcher_training": True,
            "training_with_org": "test",
            "training_passed_at": "2021-09-23 11:30:00",
        }
    )

    assert form.is_valid(), form.errors


def test_researcherregistrationform_safer_researcher_training_failed():
    form = ResearcherRegistrationForm(
        {
            "name": "test",
            "job_title": "test",
            "email": "test",
            "has_taken_safe_researcher_training": True,
        }
    )

    assert not form.is_valid()

    msg = (
        "When a researcher has undertaken safe researcher training we "
        "need to know the organisation and date they passed the course"
    )
    assert form.errors == {"__all__": [msg]}


def test_researcherregistrationform_server_access_failed():
    form = ResearcherRegistrationForm(
        {
            "name": "test",
            "job_title": "test",
            "email": "test",
            "does_researcher_need_server_access": True,
        }
    )

    assert not form.is_valid()
    assert form.errors == {
        "__all__": [
            "A phone number and phone type are required to access the results server"
        ],
    }


def test_researcherregistrationform_without_server_access_or_safe_researcher():
    form = ResearcherRegistrationForm(
        {
            "name": "test",
            "job_title": "test",
            "email": "test",
            "does_researcher_need_server_access": False,
            "has_taken_safe_researcher_training": False,
        }
    )
    assert form.is_valid(), form.errors
