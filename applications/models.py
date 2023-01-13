from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from jobserver import hash_utils


YES_NO_CHOICES = [
    (True, "Yes"),
    (False, "No"),
]


class Application(models.Model):
    class Statuses(models.TextChoices):
        APPROVED_FULLY = "approved_fully", "Approved Fully"
        APPROVED_SUBJECT_TO = "approved_subject_to", "Approved Subject To"
        COMPLETED = "completed", "Completed"
        SUBMITTED = "submitted", "Submitted"
        ONGOING = "ongoing", "Ongoing"
        REJECTED = "rejected", "Rejected"
        DEFERRED = "deferred", "Deferred"

    submitted_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        null=True,
        related_name="submitted_applications",
    )
    approved_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        null=True,
        related_name="approved_applications",
    )
    created_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        related_name="applications",
    )
    deleted_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        null=True,
        related_name="deleted_applications",
    )
    # completed application's project
    project = models.ForeignKey(
        "jobserver.Project",
        on_delete=models.SET_NULL,
        null=True,
        related_name="applications",
    )

    status = models.TextField(choices=Statuses.choices, default=Statuses.ONGOING)
    status_comment = models.TextField(default="", blank=True)
    has_agreed_to_terms = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    approved_at = models.DateTimeField(null=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(
                        approved_at__isnull=True,
                        approved_by__isnull=True,
                    )
                    | (
                        Q(
                            approved_at__isnull=False,
                            approved_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_approved_at_and_approved_by_set",
            ),
            models.CheckConstraint(
                check=(
                    Q(
                        deleted_at__isnull=True,
                        deleted_by__isnull=True,
                    )
                    | (
                        Q(
                            deleted_at__isnull=False,
                            deleted_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_deleted_at_and_deleted_by_set",
            ),
            models.CheckConstraint(
                check=(
                    Q(
                        submitted_at__isnull=True,
                        submitted_by__isnull=True,
                    )
                    | (
                        Q(
                            submitted_at__isnull=False,
                            submitted_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_submitted_at_and_submitted_by_set",
            ),
        ]

    def __str__(self):
        return f"Application {self.pk_hash} by {self.created_by.name}"

    @property
    def pk_hash(self):
        """Return the short hash identifying this Application."""
        return hash_utils.hash(self.pk)

    def get_absolute_url(self):
        return reverse("applications:detail", kwargs={"pk_hash": self.pk_hash})

    def get_approve_url(self):
        return reverse("staff:application-approve", kwargs={"pk_hash": self.pk_hash})

    def get_delete_url(self):
        return reverse("applications:delete", kwargs={"pk_hash": self.pk_hash})

    def get_edit_url(self):
        return reverse("staff:application-edit", kwargs={"pk_hash": self.pk_hash})

    def get_restore_url(self):
        return reverse("applications:restore", kwargs={"pk_hash": self.pk_hash})

    def get_staff_delete_url(self):
        return reverse("staff:application-delete", kwargs={"pk_hash": self.pk_hash})

    def get_staff_restore_url(self):
        return reverse("staff:application-restore", kwargs={"pk_hash": self.pk_hash})

    def get_staff_url(self):
        return reverse("staff:application-detail", kwargs={"pk_hash": self.pk_hash})

    @property
    def is_approved(self):
        return self.approved_at or self.approved_by

    @property
    def is_deleted(self):
        return self.deleted_at or self.deleted_by

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
        on_delete=models.PROTECT,
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


class CommercialInvolvementPage(AbstractPage):
    details = models.TextField(blank=True)


class StudyInformationPage(AbstractPage):
    study_name = models.TextField(blank=True)
    study_purpose = models.TextField(blank=True)


class StudyPurposePage(AbstractPage):
    description = models.TextField(blank=True)
    author_name = models.TextField(blank=True)
    author_email = models.TextField(blank=True)
    author_organisation = models.TextField(blank=True)
    is_covid_prevention = models.BooleanField(default=False)
    is_risk_from_covid = models.BooleanField(default=False)
    is_post_covid_health_impacts = models.BooleanField(default=False)
    is_covid_vaccine_eligibility_or_coverage = models.BooleanField(default=False)
    is_covid_vaccine_effectiveness_or_safety = models.BooleanField(default=False)
    is_other_impacts_of_covid = models.BooleanField(default=False)


class StudyDataPage(AbstractPage):
    data_meets_purpose = models.TextField(blank=True)
    need_record_level_data = models.BooleanField(null=True, choices=YES_NO_CHOICES)


class DatasetsPage(AbstractPage):
    needs_icnarc = models.BooleanField(default=False)
    needs_isaric = models.BooleanField(default=False)
    needs_ons_cis = models.BooleanField(default=False)
    needs_phosp = models.BooleanField(default=False)


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
    is_member_of_bennett_or_lshtm = models.BooleanField(default=False)


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
        on_delete=models.PROTECT,
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
    github_username = models.TextField()

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

    daa = models.URLField(null=True, blank=True)
    github_username = models.TextField(default="", blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "applications:researcher-detail",
            kwargs={"pk_hash": self.application.pk_hash, "researcher_pk": self.pk},
        )

    def get_delete_url(self):
        return reverse(
            "applications:researcher-delete",
            kwargs={"pk_hash": self.application.pk_hash, "researcher_pk": self.pk},
        )

    def get_edit_url(self):
        return reverse(
            "applications:researcher-edit",
            kwargs={"pk_hash": self.application.pk_hash, "researcher_pk": self.pk},
        )

    def get_staff_edit_url(self):
        return reverse("staff:researcher-edit", kwargs={"pk": self.pk})
