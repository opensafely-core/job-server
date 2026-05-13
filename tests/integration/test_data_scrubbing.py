import pytest
from django.core.management import call_command

from jobserver.models import User

from ..factories import UserFactory


@pytest.mark.django_db
def test_scrub_fields_are_changed_and_allowed_fields_are_not():
    user = UserFactory()
    fields_to_scrub = user.DataScrubbing.fields_to_scrub

    # Snapshot fields before scrubbing.
    before = {
        field.name: getattr(user, field.name)
        for field in User._meta.get_fields()
        if hasattr(user, field.name)
    }

    call_command("scrub_data")

    user.refresh_from_db()

    # Scrubbed fields changed to their defined replacement values.
    for field_name, fake_value in fields_to_scrub.items():
        actual = getattr(user, field_name)
        if callable(fake_value):
            # If callable we can only in general assert that the value changed.
            assert actual != before[field_name], f"{field_name} should have changed"
        else:
            expected = fields_to_scrub[field_name]
            assert actual == expected, (
                f"{field_name} should be {expected!r}, got {actual!r}"
            )

    # Other fields untouched.
    for field_name, original_value in before.items():
        if field_name in fields_to_scrub:
            continue
        assert getattr(user, field_name) == original_value, (
            f"{field_name} should not have been touched by scrubbing"
        )
