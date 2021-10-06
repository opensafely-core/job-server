from applications.form_specs import form_specs
from applications.wizard import Wizard


def test_get_next_page_key_for_complete_application(complete_application):
    wizard = Wizard(complete_application, form_specs)
    assert wizard.get_next_page_key("contact-details") is None


def test_get_next_page_key_for_incomplete_application(incomplete_application):
    wizard = Wizard(incomplete_application, form_specs)
    assert wizard.get_next_page_key("contact-details") == "study-funding"
