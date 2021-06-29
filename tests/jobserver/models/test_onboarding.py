import pytest
from django.utils import timezone

from ...factories import ResearcherRegistrationFactory


@pytest.mark.django_db
def test_researcher_registration_str():
    researcher = ResearcherRegistrationFactory(
        name="Terry",
        passed_researcher_training_at=timezone.now(),
    )
    assert str(researcher) == "Terry"
