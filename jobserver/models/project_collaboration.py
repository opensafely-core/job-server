from django.db import models


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

    is_lead = models.BooleanField(null=True)

    def __str__(self):
        suffix = " (lead)" if self.is_lead else ""
        return f"{self.org.name} <-> {self.project.name}{suffix}"
