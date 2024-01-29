from datetime import UTC

import factory
import factory.fuzzy

from applications.models import (
    Application,
    CommercialInvolvementPage,
    ContactDetailsPage,
    DatasetsPage,
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


class AbstractPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        abstract = True

    application = factory.SubFactory("tests.factories.ApplicationFactory")
    reviewed_by = factory.SubFactory("tests.factories.UserFactory")

    notes = factory.Sequence(lambda n: f"note {n}")
    is_approved = factory.fuzzy.FuzzyChoice([True, False])

    last_reviewed_at = factory.Faker("date_time", tzinfo=UTC)

    created_at = factory.Faker("date_time", tzinfo=UTC)
    updated_at = factory.Faker("date_time", tzinfo=UTC)


class ContactDetailsPageFactory(AbstractPageFactory):
    class Meta:
        model = ContactDetailsPage

    full_name = factory.Sequence(lambda n: f"name {n}")
    email = factory.Sequence(lambda n: f"name{n}@example.com")
    telephone = factory.Faker("phone_number")
    job_title = factory.Faker("job")
    team_name = factory.Sequence(lambda n: f"team {n}")
    organisation = factory.Sequence(lambda n: f"org {n}")


class CommercialInvolvementPageFactory(AbstractPageFactory):
    class Meta:
        model = CommercialInvolvementPage

    details = factory.Sequence(lambda n: f"details {n}")


class StudyInformationPageFactory(AbstractPageFactory):
    class Meta:
        model = StudyInformationPage

    study_name = factory.Sequence(lambda n: f"study {n}")
    study_purpose = factory.Sequence(lambda n: f"purpose {n}")


class StudyPurposePageFactory(AbstractPageFactory):
    class Meta:
        model = StudyPurposePage

    description = factory.Sequence(lambda n: f"description {n}")
    author_name = factory.Sequence(lambda n: f"author name {n}")
    author_email = factory.Sequence(lambda n: f"name{n}@example.com")
    author_organisation = factory.Sequence(lambda n: f"author org {n}")


class StudyDataPageFactory(AbstractPageFactory):
    class Meta:
        model = StudyDataPage

    data_meets_purpose = factory.Sequence(lambda n: f"data meets purpose {n}")
    need_record_level_data = factory.fuzzy.FuzzyChoice([True, False])


class DatasetsPageFactory(AbstractPageFactory):
    class Meta:
        model = DatasetsPage

    needs_icnarc = factory.fuzzy.FuzzyChoice([True, False])
    needs_isaric = factory.fuzzy.FuzzyChoice([True, False])
    needs_ons_cis = factory.fuzzy.FuzzyChoice([True, False])
    needs_phosp = factory.fuzzy.FuzzyChoice([True, False])
    needs_ukrr = factory.fuzzy.FuzzyChoice([True, False])


class RecordLevelDataPageFactory(AbstractPageFactory):
    class Meta:
        model = RecordLevelDataPage

    record_level_data_reasons = factory.Sequence(
        lambda n: f"record level data reasons {n}"
    )


class TypeOfStudyPageFactory(AbstractPageFactory):
    class Meta:
        model = TypeOfStudyPage

    is_study_research = factory.fuzzy.FuzzyChoice([True, False])
    is_study_service_evaluation = factory.fuzzy.FuzzyChoice([True, False])
    is_study_audit = factory.fuzzy.FuzzyChoice([True, False])


class ReferencesPageFactory(AbstractPageFactory):
    class Meta:
        model = ReferencesPage

    hra_ires_id = factory.Sequence(lambda n: f"HRA IRES ID {n}")
    hra_rec_reference = factory.Sequence(lambda n: f"HRA REC {n}")
    institutional_rec_reference = factory.Sequence(lambda n: f"Institutional REC {n}")


class SponsorDetailsPageFactory(AbstractPageFactory):
    class Meta:
        model = SponsorDetailsPage

    sponsor_name = factory.Sequence(lambda n: f"Sponsor {n}")
    sponsor_email = factory.Sequence(lambda n: f"sponsor{n}@example.com")
    sponsor_job_role = factory.Faker("job")
    institutional_rec_reference = factory.Sequence(lambda n: f"Institutional REC {n}")


class StudyFundingPageFactory(AbstractPageFactory):
    class Meta:
        model = StudyFundingPage

    funding_details = factory.Sequence(lambda n: f"funding details {n}")


class TeamDetailsPageFactory(AbstractPageFactory):
    class Meta:
        model = TeamDetailsPage

    team_details = factory.Sequence(lambda n: f"team details {n}")


class PreviousEhrExperiencePageFactory(AbstractPageFactory):
    class Meta:
        model = PreviousEhrExperiencePage

    previous_experience_with_ehr = factory.Sequence(
        lambda n: f"previous EHR experience {n}"
    )


class SoftwareDevelopmentExperiencePageFactory(AbstractPageFactory):
    class Meta:
        model = SoftwareDevelopmentExperiencePage

    evidence_of_coding = factory.Sequence(lambda n: f"evidence of coding {n}")
    all_applicants_completed_getting_started = factory.fuzzy.FuzzyChoice([True, False])


class SharingCodePageFactory(AbstractPageFactory):
    class Meta:
        model = SharingCodePage

    evidence_of_sharing_in_public_domain_before = factory.Sequence(
        lambda n: f"sharing in public domain {n}"
    )


class ResearcherDetailsPageFactory(AbstractPageFactory):
    class Meta:
        model = ResearcherDetailsPage


class ResearcherRegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResearcherRegistration

    application = factory.SubFactory("tests.factories.ApplicationFactory")
    has_taken_safe_researcher_training = True
    training_passed_at = factory.Faker("date_time", tzinfo=UTC)
