import pytest
from django.apps import apps
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


@pytest.mark.xfail(reason="Not finished initial categorisation yet")
def test_all_applications_fields_categorised():
    models = {model for model in apps.get_app_config("applications").get_models()}

    models_with_no_configuration = set()
    fields_not_categorised = {}

    for model in models:
        dotted_path = f"{model.__module__}.{model.__name__}"
        data_scrubbing = getattr(model, "DataScrubbing", None)

        if data_scrubbing is None:
            models_with_no_configuration.add(dotted_path)
            continue
        fields_to_scrub_dict = getattr(data_scrubbing, "fields_to_scrub", {})
        fields_to_scrub = set(fields_to_scrub_dict.keys())
        allowed_fields = getattr(data_scrubbing, "allowed_fields", set())

        all_model_fields = {f.name for f in model._meta.fields}
        uncategorised_fields = all_model_fields - fields_to_scrub - allowed_fields
        if uncategorised_fields:
            fields_not_categorised[dotted_path] = uncategorised_fields

    hint = (
        "Each model must define a `DataScrubbing` inner class specifying "
        "`fields_to_scrub` (a dict of field name -> scrubbing strategy) and/or "
        "`allowed_fields` (a set of field names that don't need scrubbing) "
        "so that every field is explicitly categorised. They must not overlap.\n"
        "Refer to the documentation of the data_scrubbing module."
    )

    if models_with_no_configuration:
        missing_list = "\n".join(
            f"  - {name}" for name in sorted(models_with_no_configuration)
        )
        pytest.fail(
            f"{len(models_with_no_configuration)} model(s) are missing a "
            f"`DataScrubbing` inner class entirely:\n"
            f"{missing_list}\n\n"
            f"{hint}"
        )

    if fields_not_categorised:
        details = "\n".join(
            f"  - {name}:\n"
            + "\n".join(f'{" " * 16}"{field}",' for field in sorted(fields))
            for name, fields in sorted(fields_not_categorised.items())
        )
        pytest.fail(
            f"{len(fields_not_categorised)} model(s) have fields not included in "
            f"their `DataScrubbing` inner class:\n"
            f"{details}\n\n"
            f"{hint}"
        )
