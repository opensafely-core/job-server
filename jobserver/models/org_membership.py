import structlog
from django.db import models
from django.utils import timezone


logger = structlog.get_logger(__name__)


class OrgMembership(models.Model):
    """Membership of an Organistion for a User"""

    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="created_org_memberships",
        null=True,
    )
    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="org_memberships",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class DataScrubbing:
        fields_to_scrub = {}
        # Institutional affiliation as represented by the link between an Org
        # and a User is Personal Data. User.username is also Personal Data and
        # is not scrubbed, so it can identify the user associated with a
        # membership. However, usernames are not especially sensitive because
        # they are already public on the production Job Server and probably
        # elsewhere as well.
        #
        # We could remove all OrgMembership data or permute the relations, but
        # as it is relational data this is more difficult, and this would make
        # some kinds of testing harder. We could try to pseudonymise this data
        # somewhat by changing the Org names to fake ones, but the structure of
        # the database still reveals which org it is when combined with which
        # studies they are involved with et cetera.
        #
        # We decided the minimal privacy benefit of doing this was not worth
        # the technical difficulty.
        allowed_fields = frozenset(
            [
                "id",
                "created_at",
                "created_by",
                "org",
                "user",
            ]
        )

    class Meta:
        unique_together = ["org", "user"]

    def __str__(self):
        return f"{self.user.username} | {self.org.name}"
