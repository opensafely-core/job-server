from urllib.parse import quote

import structlog
from django.db import models
from django.db.models import Q
from django.urls import reverse
from furl import furl


logger = structlog.get_logger(__name__)


class Repo(models.Model):
    url = models.TextField(unique=True)
    has_github_outputs = models.BooleanField(default=False)

    internal_signed_off_at = models.DateTimeField(null=True)
    internal_signed_off_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="internally_signed_off_repos",
        null=True,
    )

    researcher_signed_off_at = models.DateTimeField(null=True)
    researcher_signed_off_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        null=True,
        related_name="repos_signed_off_by_researcher",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(
                        internal_signed_off_at__isnull=True,
                        internal_signed_off_by__isnull=True,
                    )
                    | (
                        Q(
                            internal_signed_off_at__isnull=False,
                            internal_signed_off_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_internal_signed_off_at_and_internal_signed_off_by_set",
            ),
            models.CheckConstraint(
                check=(
                    Q(
                        researcher_signed_off_at__isnull=True,
                        researcher_signed_off_by__isnull=True,
                    )
                    | (
                        Q(
                            researcher_signed_off_at__isnull=False,
                            researcher_signed_off_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_researcher_signed_off_at_and_researcher_signed_off_by_set",
            ),
        ]

    def __str__(self):
        return self.url

    def get_handler_url(self):
        return reverse("repo-handler", kwargs={"repo_url": self.quoted_url})

    def get_sign_off_url(self):
        return reverse("repo-sign-off", kwargs={"repo_url": self.quoted_url})

    def get_staff_sign_off_url(self):
        return reverse("staff:repo-sign-off", kwargs={"repo_url": self.quoted_url})

    def get_staff_url(self):
        return reverse("staff:repo-detail", kwargs={"repo_url": self.quoted_url})

    @property
    def name(self):
        """Convert repo URL -> repo name"""
        return self._url().path.segments[-1]

    @property
    def owner(self):
        """Convert repo URL -> repo owner"""
        return self._url().path.segments[0]

    @property
    def quoted_url(self):
        return quote(self.url, safe="")

    def _url(self):
        f = furl(self.url)

        if not f.path:
            raise Exception("Repo URL not in expected format, appears to have no path")

        return f
