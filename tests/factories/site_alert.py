from datetime import UTC

import factory

from jobserver.models import SiteAlert


class SiteAlertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SiteAlert

    title = factory.Sequence(lambda n: f"SiteAlert title {n}")
    message = factory.Sequence(lambda n: f"SiteAlert message {n}")
    level = factory.Faker("random_element", elements=SiteAlert.Level.values)

    created_at = factory.Faker("date_time", tzinfo=UTC)
    updated_at = factory.Faker("date_time", tzinfo=UTC)
    created_by = factory.SubFactory("tests.factories.UserFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")
