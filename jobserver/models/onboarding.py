from django.db import models
from django.utils import timezone


class ResearcherRegistration(models.Model):
    """
    The Registration of a Researcher for a Project

    When registering a new Project 0-N researchers might be named as part of
    the Project.  Instead of requiring they sign up to the service during the
    registration process this model holds their details, and can be attached to
    a User instance if the Project proceeds past registration.
    """

    user = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="researcher_registrations",
    )

    name = models.TextField()
    passed_researcher_training_at = models.DateTimeField()
    is_ons_accredited_researcher = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
