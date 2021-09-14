from django.db import models
from django.utils import timezone


class Application(models.Model):
    # completed application's project
    project = models.ForeignKey(
        "jobserver.Project",
        on_delete=models.SET_NULL,
        null=True,
        related_name="applications",
    )

    # form 1 (contact details)
    full_name = models.TextField()
    email = models.TextField(blank=True)
    telephone = models.TextField(blank=True)
    job_title = models.TextField(blank=True)
    team_name = models.TextField(blank=True)

    # TODO: how will we tie this to an existing org, especially with typos?
    organisation = models.TextField(blank=True)

    # form 2 (study information)
    study_name = models.TextField(blank=True)
    purpose = models.TextField(blank=True)

    # form 3 (study purpose)
    purpose = models.TextField(blank=True)
    author_name = models.TextField(blank=True)
    author_email = models.TextField(blank=True)
    author_organisation = models.TextField(blank=True)

    # form 4 (study data)
    study_data = models.TextField(blank=True)
    need_record_level_data = models.BooleanField(null=True, default=None)

    # form 5 (record level data)
    record_level_data_reasons = models.TextField(blank=True)

    # form 6 (ethical and sponsor requirements)
    is_study_research = models.BooleanField(null=True, default=None)
    is_study_a_service_evaluation = models.BooleanField(null=True, default=None)

    # form 7 (ethical and sponsor requirements)
    hra_ires_id = models.TextField(blank=True)
    hra_rec_reference = models.TextField(blank=True)
    institutional_rec_reference = models.TextField(blank=True)

    # form 8 (ethical and sponsor requirements)
    # institutional_rec_reference = models.TextField(blank=True)

    # form 9 (cmo priority)
    is_on_cmo_priority_list = models.BooleanField(null=True, default=None)

    # form 10 (study funding)
    funding_details = models.TextField(blank=True)

    # form 11 (team details)
    team_details = models.TextField(blank=True)

    # form 12 (electronic health record data)
    previous_experience_with_ehr = models.TextField(blank=True)

    # form 13 (coding)
    evidence_of_coding = models.TextField(blank=True)

    # form 14 (public domain)
    evidence_of_sharing_in_public_domain_before = models.TextField(blank=True)

    # form 15
    number_of_researchers_needing_access = models.IntegerField(default=0)

    has_agreed_to_terms = models.BooleanField(null=True, default=None)


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
    github_username = models.TextField()
    telephone = models.TextField()
    phone_type = models.TextField(choices=PhoneTypes.choices)

    has_taken_safe_researcher_training = models.BooleanField()
    training_with_org = models.TextField()
    training_passed_at = models.DateTimeField()

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
