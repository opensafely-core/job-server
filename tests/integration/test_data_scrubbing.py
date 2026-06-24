import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from data_scrubbing.management.commands.scrub_data import get_scrubbed_models

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
    """Test that the scrub_data command does replace sensitive fields according
    to its configuration.

    See the data_scrubbing package to better understand this functionality."""
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


def _details_str(model_dict):
    """String listing apps and fields in model_dict formatted nicely."""
    return "\n".join(
        f"  - {name}:\n"
        + "\n".join(f'{" " * 16}"{field}",' for field in sorted(fields))
        for name, fields in sorted(model_dict.items())
    )


def test_details_str_formats_model_dict():
    """Test that _details_str can format a model dict."""
    model_dict = {
        "app.models.Foo": {"alpha", "beta"},
        "app.models.Bar": {"gamma"},
    }
    result = _details_str(model_dict)
    assert result == (
        "  - app.models.Bar:\n"
        '                "gamma",\n'
        "  - app.models.Foo:\n"
        '                "alpha",\n'
        '                "beta",'
    )


def test_all_scrubbed_model_fields_categorised():
    """Test that each model in `get_scrubbed_models` has a DataScrubbing class
    that includes all its concrete fields.

    Each model must define a `DataScrubbing` inner class specifying
    `fields_to_scrub` (a dict of field name -> scrubbing strategy) and/or
    `allowed_fields` (a set of field names that don't need scrubbing) so that
    every concrete field is explicitly categorised. They must not overlap.

    Refer to the documentation of the data_scrubbing module."""
    models_with_no_configuration = set()
    """Set of model dotted paths that have on DataScrubbing configuration."""
    fields_not_categorised = {}
    """Dict mapping model dotted paths to list of fields missing from DataScrubbing."""
    extra_fields = {}
    """Dict mapping model dotted paths to list of extra fields in DataScrubbing."""
    duplicated_fields = {}
    """Dict mapping model dotted paths to list of fields duplicated in DataScrubbing."""

    for model in get_scrubbed_models():
        # Check that the model has DataScrubbing configuration.
        dotted_path = f"{model.__module__}.{model.__name__}"
        data_scrubbing = getattr(model, "DataScrubbing", None)

        if data_scrubbing is None:  # pragma: no cover
            models_with_no_configuration.add(dotted_path)
            continue

        # Check for uncategorised, extra and duplicated fields with set operations.
        fields_to_scrub_dict = getattr(data_scrubbing, "fields_to_scrub", {})
        fields_to_scrub = set(fields_to_scrub_dict.keys())
        allowed_fields = getattr(data_scrubbing, "allowed_fields", set())
        all_model_fields = {f.name for f in model._meta.fields}

        uncategorised_fields = all_model_fields - fields_to_scrub - allowed_fields
        if uncategorised_fields:  # pragma: no cover
            fields_not_categorised[dotted_path] = uncategorised_fields

        extras = (fields_to_scrub | allowed_fields) - all_model_fields
        if extras:  # pragma: no cover
            extra_fields[dotted_path] = extras

        duplicates = fields_to_scrub & allowed_fields
        if duplicates:  # pragma: no cover
            duplicated_fields[dotted_path] = duplicates

    # Assertions on the results of the above.
    hint = (
        "Each model must define a `DataScrubbing` inner class specifying "
        "`fields_to_scrub` (a dict of field name -> scrubbing strategy) and/or "
        "`allowed_fields` (a set of field names that don't need scrubbing) "
        "so that every field is explicitly categorised. They must not overlap.\n"
        "Refer to the documentation of the data_scrubbing module."
    )

    if models_with_no_configuration:  # pragma: no cover
        missing_list = "\n".join(
            f"  - {name}" for name in sorted(models_with_no_configuration)
        )
        pytest.fail(
            f"{len(models_with_no_configuration)} model(s) are missing a "
            f"`DataScrubbing` inner class entirely:\n"
            f"{missing_list}\n\n"
            f"{hint}"
        )

    if fields_not_categorised:  # pragma: no cover
        details = _details_str(fields_not_categorised)
        pytest.fail(
            f"{len(fields_not_categorised)} model(s) have fields not included in "
            f"their `DataScrubbing` inner class:\n{details}\n\n{hint}"
        )

    if extra_fields:  # pragma: no cover
        details = _details_str(extra_fields)
        pytest.fail(
            f"{len(extra_fields)} model(s) have extra fields included in "
            f"their `DataScrubbing` inner class:\n{details}\n\n{hint}"
        )

    if duplicated_fields:  # pragma: no cover
        details = _details_str(duplicated_fields)
        pytest.fail(
            f"{len(duplicated_fields)} model(s) have fields included in both "
            f"`fields_to_scrub` and in `allowed_fields` in "
            f"their `DataScrubbing` inner class:\n{details}\n\n{hint}"
        )
