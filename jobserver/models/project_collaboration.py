from django.db import models
from django.db.models import Q


class ProjectCollaboration(models.Model):
    org = models.ForeignKey(
        "Org",
        on_delete=models.PROTECT,
        related_name="project_orgs",
    )
    project = models.ForeignKey(
        "Project",
        on_delete=models.PROTECT,
        related_name="project_orgs",
    )

    is_lead = models.BooleanField(default=False)

    def __str__(self):
        suffix = " (lead)" if self.is_lead else ""
        return f"{self.org.name} <-> {self.project.name}{suffix}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project"],
                condition=Q(is_lead=True),
                name="%(app_label)s_%(class)s_only_one_lead_org_set",
            )
        ]
        unique_together = ["org", "project"]
