import factory
from pytz import utc

from applications.models import (
    Application,
    CmoPriorityListPage,
    ContactDetailsPage,
    LegalBasisPage,
    PreviousEhrExperiencePage,
    RecordLevelDataPage,
    ReferencesPage,
    ResearcherDetailsPage,
    ResearcherRegistration,
    SharingCodePage,
    SoftwareDevelopmentExperiencePage,
    SponsorDetailsPage,
    StudyDataPage,
    StudyFundingPage,
    StudyInformationPage,
    StudyPurposePage,
    TeamDetailsPage,
    TypeOfStudyPage,
)


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Application

    created_by = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")


class ContactDetailsPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContactDetailsPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class StudyInformationPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudyInformationPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class StudyPurposePageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudyPurposePage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class StudyDataPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudyDataPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class RecordLevelDataPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RecordLevelDataPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class TypeOfStudyPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TypeOfStudyPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class ReferencesPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReferencesPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class SponsorDetailsPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SponsorDetailsPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class CmoPriorityListPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CmoPriorityListPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class LegalBasisPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LegalBasisPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class StudyFundingPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudyFundingPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class TeamDetailsPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamDetailsPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class PreviousEhrExperiencePageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PreviousEhrExperiencePage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class SoftwareDevelopmentExperiencePageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SoftwareDevelopmentExperiencePage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class SharingCodePageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SharingCodePage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class ResearcherDetailsPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResearcherDetailsPage

    application = factory.SubFactory("tests.factories.ApplicationFactory")


class ResearcherRegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResearcherRegistration

    application = factory.SubFactory("tests.factories.ApplicationFactory")

    has_taken_safe_researcher_training = True
    training_passed_at = factory.Faker("date_time", tzinfo=utc)
