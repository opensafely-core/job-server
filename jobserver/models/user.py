import itertools
import secrets
import unicodedata
from datetime import date, timedelta

import structlog
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from sentry_sdk import capture_message

from ..authorization.fields import RolesArrayField
from ..hash_utils import hash_user_pat


logger = structlog.get_logger(__name__)


class UserManager(models.Manager):
    use_in_migrations = True

    def create(self, **kwargs):
        # Normalize email to lowercase. RFC 5321 §2.4 states that the local
        # part of an email (before the @ symbol) must be treated as
        # case-sensitive by SMTP. However, mail systems are encouraged to
        # handle it in a case-insensitive manner for local delivery, and almost
        # all follow this recommendation.
        # Without normalization, `unique=True` on an EmailField would allow
        # duplicate entries like `User@example.com` and `user@example.com`.
        # This risk outweighs the rare possibility of a case-sensitive mail
        # system. Currently, this issue is moot as users don't manually enter
        # their email.
        kwargs["email"] = kwargs.get("email", "").lower()
        # Normalize username unicode to avoid multiple representations of the same
        # username.
        kwargs["username"] = unicodedata.normalize("NFKC", kwargs.get("username", ""))
        password = kwargs.pop("password", None)
        if password:
            kwargs["password"] = make_password(password)

        return super().create(**kwargs)


class User(AbstractBaseUser):
    """
    A User of the site.

    Changing any fields in the User model may require the corresponding
    view, used by Grafana, to be regenerated after deployment. More
    information can be found in https://github.com/ebmdatalab/metrics/blob/main/grafana/README.md
    """

    backends = models.ManyToManyField(
        "Backend",
        related_name="members",
        through="BackendMembership",
        through_fields=["user", "backend"],
    )
    orgs = models.ManyToManyField(
        "Org",
        related_name="members",
        through="OrgMembership",
        through_fields=["user", "org"],
    )
    projects = models.ManyToManyField(
        "Project",
        related_name="members",
        through="ProjectMembership",
        through_fields=["user", "project"],
    )

    username_validator = UnicodeUsernameValidator()
    username = models.TextField(
        unique=True,
        validators=[username_validator],
        error_messages={"unique": "A user with that username already exists."},
    )
    email = models.EmailField(blank=True, unique=True)

    # 'fullname' instead of 'full_name' because social auth already uses
    # 'fullname' and life is too short to work out which classes we should map
    # 'fullname' -> 'full_name' in.
    fullname = models.TextField()

    date_joined = models.DateTimeField("date joined", default=timezone.now)

    # PATs are generated for bot users.  They can only be generated via a shell
    # so they can't be accidentally exposed via the UI.
    pat_token = models.TextField(null=True, unique=True)
    pat_expires_at = models.DateTimeField(null=True)

    # Single use token login.
    login_token = models.TextField(null=True)
    login_token_expires_at = models.DateTimeField(null=True)

    created_by = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
    )

    roles = RolesArrayField()

    objects = UserManager()

    # Used by AbstractBaseUser machinery we possibly need.
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"

    class Meta:
        constraints = [
            # pat_* fields are null together, or not.
            models.CheckConstraint(
                condition=(
                    Q(
                        pat_expires_at__isnull=True,
                        pat_token__isnull=True,
                    )
                    | Q(
                        pat_expires_at__isnull=False,
                        pat_token__isnull=False,
                    )
                ),
                name="%(app_label)s_%(class)s_both_pat_expires_at_and_pat_token_set",
            ),
            models.CheckConstraint(
                condition=~Q(fullname=""),
                name="fullname_non_blank",
            ),
        ]
        ordering = [
            # Order by fullname then username, case-insensitive.
            Lower("fullname"),
            Lower("username"),
        ]

    def __str__(self):
        return self.fullname

    @cached_property
    def has_any_roles(self):
        project_roles = list(
            itertools.chain.from_iterable(
                [m.roles for m in self.project_memberships.all()]
            )
        )
        return any(self.roles + project_roles)

    @property
    def initials(self):
        if self.fullname == self.username:
            return self.fullname[0].upper()

        return "".join(w[0].upper() for w in self.fullname.split(" "))

    def get_absolute_url(self):
        return reverse("user-detail", kwargs={"username": self.username})

    def get_all_permissions(self):
        """
        Get all Permissions for the current User.
        """

        def flatten_perms(roles):
            permissions = itertools.chain.from_iterable(r.permissions for r in roles)
            return list(sorted(set(permissions)))

        projects = [
            {
                "slug": m.project.slug,
                "permissions": flatten_perms(m.roles),
            }
            for m in self.project_memberships.all()
        ]

        return {
            "global": flatten_perms(self.roles),
            "projects": projects,
        }

    def get_all_roles(self):
        """
        Get all Roles for the current User.

        Return all Roles for the User, grouping the local-Roles by the objects
        they are contextual to.
        """

        def role_names(roles):
            return list(sorted(r.__name__ for r in roles))

        projects = [
            {"slug": m.project.slug, "roles": role_names(m.roles)}
            for m in self.project_memberships.all()
        ]

        return {
            "global": role_names(self.roles),
            "projects": projects,
        }

    def get_full_name(self):
        """Support Django's User contract"""
        return self.fullname

    def get_logs_url(self):
        return reverse("user-event-log", kwargs={"username": self.username})

    def get_staff_audit_url(self):
        return reverse("staff:user-audit-log", kwargs={"username": self.username})

    def get_staff_clear_roles_url(self):
        return reverse("staff:user-clear-roles", kwargs={"username": self.username})

    def get_staff_roles_url(self):
        return reverse("staff:user-role-list", kwargs={"username": self.username})

    def get_staff_url(self):
        return reverse("staff:user-detail", kwargs={"username": self.username})

    def has_valid_pat(self, full_token):
        if not full_token:
            return False

        pat_token = hash_user_pat(full_token)
        if not secrets.compare_digest(pat_token, self.pat_token):
            return False

        if self.pat_expires_at.date() < date.today():
            capture_message(f"Expired token for {self.username}")
            return False

        return True

    def rotate_token(self):
        # Ticket to look at signing request.
        expires_at = timezone.now() + timedelta(days=90)

        # Store as datetime in case we want to compare with a datetime or
        # increase resolution later.
        expires_at = expires_at.replace(hour=0, minute=0, second=0, microsecond=0)

        # Suffix the token with the expiry date so it's clearer to users of it
        # when it will expire.
        token = f"{secrets.token_hex(32)}-{expires_at.date().isoformat()}"

        # We're going to check the token against ones passed to the service,
        # but we don't want to expose ourselves to timing attacks.  So we're
        # storing it in the db as a hased string using Django's password
        # hashing tools and then comparing (in User.is_valid_pat()) with
        # secrets.compare_digest to avoid a timing attack there.
        hashed_token = hash_user_pat(token)

        self.pat_expires_at = expires_at
        self.pat_token = hashed_token
        self.save(update_fields=["pat_token", "pat_expires_at"])

        # Return the unhashed token so it can be passed to a consuming service.
        return token

    @cached_property
    def uses_social_auth(self):
        """
        Cache whether this user logs in via GitHub (using social auth).

        We use this in a couple of places in our base header template, so to
        avoid extra queries on every page load we're caching it to the user
        instance here.
        """
        return self.social_auth.exists()
