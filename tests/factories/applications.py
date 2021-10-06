import factory
from pytz import utc

from applications.models import Application, ResearcherRegistration


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Application

    created_by = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")


class ResearcherRegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResearcherRegistration

    application = factory.SubFactory("tests.factories.ApplicationFactory")

    has_taken_safe_researcher_training = True
    training_passed_at = factory.Faker("date_time", tzinfo=utc)
