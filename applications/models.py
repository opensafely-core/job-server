from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils import timezone


YES_NO_CHOICES = [
    (True, "Yes"),
    (False, "No"),
]


class Application(models.Model):
    created_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    # completed application's project
    project = models.ForeignKey(
        "jobserver.Project",
        on_delete=models.SET_NULL,
        null=True,
        related_name="applications",
    )

    has_agreed_to_terms = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True)

    has_reached_confirmation = models.BooleanField(default=False)

    def __str__(self):
        return f"Application {self.pk} by {self.created_by.name}"

    def get_absolute_url(self):
        return reverse("applications:detail", kwargs={"pk": self.pk})

    def get_staff_url(self):
        return reverse("staff:application-detail", kwargs={"pk": self.pk})

    @property
    def is_study_research(self):
        try:
            return self.typeofstudypage.is_study_research
        except ObjectDoesNotExist:
            return False

    @property
    def is_study_service_evaluation(self):
        try:
            return self.typeofstudypage.is_study_service_evaluation
        except ObjectDoesNotExist:
            return False

    @property
    def is_study_audit(self):
        try:
            return self.typeofstudypage.is_study_audit
        except ObjectDoesNotExist:
            return False


class AbstractPage(models.Model):
    application = models.OneToOneField("Application", on_delete=models.CASCADE)
    reviewed_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.CASCADE,
        null=True,
    )

    notes = models.TextField(blank=True)
    is_approved = models.BooleanField(null=True)
    last_reviewed_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ContactDetailsPage(AbstractPage):
    full_name = models.TextField()
    email = models.TextField(blank=True)
    telephone = models.TextField(blank=True)
    job_title = models.TextField(blank=True)
    team_name = models.TextField(blank=True)
    # TODO: how will we tie this to an existing org, especially with typos?
    organisation = models.TextField(blank=True)


class StudyInformationPage(AbstractPage):
    study_name = models.TextField(blank=True)
    study_purpose = models.TextField(blank=True)


class StudyPurposePage(AbstractPage):
    description = models.TextField(blank=True)
    author_name = models.TextField(blank=True)
    author_email = models.TextField(blank=True)
    author_organisation = models.TextField(blank=True)


class StudyDataPage(AbstractPage):
    data_meets_purpose = models.TextField(blank=True)
    need_record_level_data = models.BooleanField(null=True, choices=YES_NO_CHOICES)


class RecordLevelDataPage(AbstractPage):
    record_level_data_reasons = models.TextField(blank=True)


class TypeOfStudyPage(AbstractPage):
    is_study_research = models.BooleanField(default=False)
    is_study_service_evaluation = models.BooleanField(default=False)
    is_study_audit = models.BooleanField(default=False)


class ReferencesPage(AbstractPage):
    hra_ires_id = models.TextField(blank=True)
    hra_rec_reference = models.TextField(blank=True)
    institutional_rec_reference = models.TextField(blank=True)


class SponsorDetailsPage(AbstractPage):
    sponsor_name = models.TextField(blank=True)
    sponsor_email = models.TextField(blank=True)
    sponsor_job_role = models.TextField(blank=True)
    institutional_rec_reference = models.TextField(blank=True)


class CmoPriorityListPage(AbstractPage):
    is_on_cmo_priority_list = models.BooleanField(null=True, choices=YES_NO_CHOICES)


class LegalBasisPage(AbstractPage):
    legal_basis_for_accessing_data_under_dpa = models.TextField(blank=True)
    how_is_duty_of_confidentiality_satisfied = models.TextField(blank=True)


class StudyFundingPage(AbstractPage):
    funding_details = models.TextField(blank=True)


class TeamDetailsPage(AbstractPage):
    team_details = models.TextField(blank=True)


class PreviousEhrExperiencePage(AbstractPage):
    previous_experience_with_ehr = models.TextField(blank=True)


class SoftwareDevelopmentExperiencePage(AbstractPage):
    evidence_of_coding = models.TextField(blank=True)
    all_applicants_completed_getting_started = models.BooleanField(
        null=True, choices=YES_NO_CHOICES
    )


class SharingCodePage(AbstractPage):
    evidence_of_sharing_in_public_domain_before = models.TextField(blank=True)


class ResearcherDetailsPage(AbstractPage):
    pass


class ResearcherRegistration(models.Model):
    """
    The Registration of a Researcher for a Project

    When registering a new Project 0-N researchers might be named as part of
    the Project.  Instead of requiring they sign up to the service during the
    registration process this model holds their details, and can be attached to
    a User instance if the Project proceeds past registration.
    """

    class PhoneTypes(models.TextChoices):
        ANDROID = "android", "Android"
        IPHONE = "iphone", "iPhone"

    application = models.ForeignKey(
        "Application",
        on_delete=models.CASCADE,
        related_name="researcher_registrations",
    )
    user = models.ForeignKey(
        "jobserver.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="researcher_registrations",
    )

    name = models.TextField()
    job_title = models.TextField()
    email = models.TextField()

    does_researcher_need_server_access = models.BooleanField(
        null=True, choices=YES_NO_CHOICES
    )
    telephone = models.TextField(blank=True)
    phone_type = models.TextField(blank=True, choices=PhoneTypes.choices, default="")

    has_taken_safe_researcher_training = models.BooleanField(
        null=True, choices=YES_NO_CHOICES
    )
    training_with_org = models.TextField(blank=True)
    training_passed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def get_delete_url(self):
        return reverse(
            "applications:researcher-delete",
            kwargs={"pk": self.application.pk, "researcher_pk": self.pk},
        )

    def get_edit_url(self):
        return reverse(
            "applications:researcher-edit",
            kwargs={"pk": self.application.pk, "researcher_pk": self.pk},
        )
