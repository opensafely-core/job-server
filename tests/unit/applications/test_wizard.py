from django.utils import timezone

from applications.form_specs import form_specs
from applications.wizard import Wizard

from ...factories import ResearcherRegistrationFactory


def test_is_valid_false(complete_application):
    wizard = Wizard(complete_application, form_specs)

    # create a ResearcherRegistration with no values so we know the wizard is
    # invalid because of that and not the application and its pages.
    ResearcherRegistrationFactory(application=complete_application)

    assert not wizard.is_valid()


def test_is_valid(complete_application):
    wizard = Wizard(complete_application, form_specs)
    ResearcherRegistrationFactory(
        application=complete_application,
        name="ben",
        email="ben@example.com",
        job_title="The Boss",
        does_researcher_need_server_access=True,
        telephone="07777777777",
        phone_type="iphone",
        has_taken_safe_researcher_training=True,
        training_with_org="Oxford",
        training_passed_at=timezone.now(),
    )
    assert wizard.is_valid()


def test_get_next_page_key_for_complete_application(complete_application):
    wizard = Wizard(complete_application, form_specs)
    assert wizard.get_next_page_key("contact-details") is None


def test_get_next_page_key_for_incomplete_application(incomplete_application):
    wizard = Wizard(incomplete_application, form_specs)
    assert wizard.get_next_page_key("study-data") == "team-details"


def test_progress_percent(complete_application, incomplete_application):
    wizard = Wizard(complete_application, form_specs)
    assert wizard.progress_percent() == 100

    wizard = Wizard(incomplete_application, form_specs)
    assert 0 < wizard.progress_percent() < 100
