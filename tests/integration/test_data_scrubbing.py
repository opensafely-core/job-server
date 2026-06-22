import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from ..factories import (
    BackendFactory,
    ContactDetailsPageFactory,
    ResearcherRegistrationFactory,
    SponsorDetailsPageFactory,
    StudyPurposePageFactory,
    UserFactory,
)


@pytest.mark.django_db
@pytest.mark.slow_test
def test_scrub_data_command_success():
    instances = [
        UserFactory(),
        BackendFactory(),
        ContactDetailsPageFactory(),
        ResearcherRegistrationFactory(),
        SponsorDetailsPageFactory(),
        StudyPurposePageFactory(),
    ]

    # Snapshot fields before scrubbing.
    before_by_instance = {
        instance: {
            field.name: getattr(instance, field.name)
            for field in type(instance)._meta.get_fields()
            if hasattr(instance, field.name)
        }
        for instance in instances
    }

    call_command("scrub_data", "default", "--i-am-sure")

    # For each instance check that scrubbing was applied according
    # to the configuration in DataScrubbing. Manually specifying
    # all the expected fields in the test would be too onerous and
    # brittle, so let's allow using the configuration here.
    for instance in instances:
        model_class = type(instance)
        fields_to_scrub = instance.DataScrubbing.fields_to_scrub
        before = before_by_instance[instance]

        instance.refresh_from_db()

        # Scrubbed fields changed to their defined replacement values.
        for field_name, fake_value in fields_to_scrub.items():
            actual = getattr(instance, field_name)
            if callable(fake_value):
                assert actual != before[field_name], (
                    f"{model_class.__name__}.{field_name} should have changed"
                )
            else:
                expected = fields_to_scrub[field_name]
                assert actual == expected, (
                    f"{model_class.__name__}.{field_name} should be {expected!r}, got {actual!r}"
                )

        # Other fields untouched.
        for field_name, original_value in before.items():
            if field_name in fields_to_scrub:
                continue
            assert getattr(instance, field_name) == original_value, (
                f"{model_class.__name__}.{field_name} should not have been touched by scrubbing"
            )


def test_scrub_data_command_require_confirmation_on_default_database():
    with pytest.raises(CommandError, match="Use --i-am-sure"):
        call_command("scrub_data", "default")
