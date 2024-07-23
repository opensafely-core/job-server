import itertools
import secrets
from datetime import date, timedelta

import structlog
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower, NullIf
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from sentry_sdk import capture_message

from ..authorization import CoreDeveloper, InteractiveReporter
from ..authorization.fields import RolesArrayField
from ..hash_utils import hash_user_pat


logger = structlog.get_logger(__name__)


class UserQuerySet(models.QuerySet):
    def order_by_name(self):
        """
        Order Users by their "name"

        we don't have fullname populated for all users yet and having some
        users at the top of the list with just usernames looks fairly odd.
        We've modelled our text fields in job-server such that they're not
        nullable because we treat empty string as the only empty case.  The
        NullIf() call lets us tell the database to treat empty strings as NULL
        for the purposes of this ORDER BY, using nulls_last=True

        TODO: remove this method in favour of order_by(Lower("fullname")) once
        all users have fullname populated
        """
        return self.order_by(
            NullIf(
                Lower("fullname"), models.Value(""), output_field=models.TextField()
            ).asc(nulls_last=True)
        )


class UserManager(DjangoUserManager.from_queryset(UserQuerySet)):
    use_in_migrations = True

    def create_superuser(self, email, password, **extra_fields):
        username = email
        return super().create_superuser(
            username, email, password, roles=[CoreDeveloper]
        )


def get_or_create_user(username, email, fullname, update_fields=None):
    """Extend the special User.objects.create_user constructor to have the
    usual get_or_create semantics.

    By default, it will not update an existing user with the supplied email or
    fullname, but the caller can specify to do so independently for each. This
    enables a better implementation for the create_user function.
    """
    # We cannot use get_or_create here because the create_user factory function
    # is special, and does additional work when creating users.
    created = False
    try:
        user = User.objects.get(username=username)
        if update_fields:
            if "email" in update_fields:
                user.email = email
            if "fullname" in update_fields:
                user.fullname = fullname
            user.save()
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username, email=email, fullname=fullname
        )
        created = True

    return user, created


class User(AbstractBaseUser):
    """
    A custom User model used throughout the codebase

    Using a custom Model allows us to add extra fields trivially, eg Roles.
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

    # fullname instead of full_name because social auth already provides that
    # field name and life is too short to work out which class we should map
    # fullname -> full_name in.
    # TODO: rename name and remove the name property once all users have filled
    # in their names
    fullname = models.TextField(default="")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField("date joined", default=timezone.now)

    # PATs are generated for bot users.  They can only be generated via a shell
    # so they can't be accidentally exposed via the UI.
    pat_token = models.TextField(null=True, unique=True)
    pat_expires_at = models.DateTimeField(null=True)

    # single use token login
    login_token = models.TextField(null=True)
    login_token_expires_at = models.DateTimeField(null=True)

    # normally this would be nullable but we are only creating users for
    # Interactive users currently
    created_by = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
    )

    roles = RolesArrayField()

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
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
        ]

    def __str__(self):
        return self.name

    @cached_property
    def all_roles(self):
        """
        All roles, including those given via memberships, for the User

        Typically we look up whether the user has permission or a role in the
        context of another object (eg a project).  However there are times when
        we want to check all the roles available to a user.  This property
        allows us to use typical python membership checks when doing that, eg:

            if InteractiveReporter not in user.all_roles:
        """
        membership_roles = list(
            itertools.chain.from_iterable(
                [m.roles for m in self.project_memberships.all()]
                + [m.roles for m in self.org_memberships.all()]
            )
        )

        return set(self.roles + membership_roles)

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    @property
    def initials(self):
        if self.name == self.username:
            return self.name[0].upper()

        return "".join(w[0].upper() for w in self.name.split(" "))

    def get_absolute_url(self):
        return reverse("user-detail", kwargs={"username": self.username})

    def get_all_permissions(self):
        """
        Get all Permissions for the current User
        """

        def flatten_perms(roles):
            permissions = itertools.chain.from_iterable(r.permissions for r in roles)
            return list(sorted(set(permissions)))

        orgs = [
            {
                "slug": m.org.slug,
                "permissions": flatten_perms(m.roles),
            }
            for m in self.org_memberships.all()
        ]

        projects = [
            {
                "slug": m.project.slug,
                "permissions": flatten_perms(m.roles),
            }
            for m in self.project_memberships.all()
        ]

        return {
            "global": flatten_perms(self.roles),
            "orgs": orgs,
            "projects": projects,
        }

    def get_all_roles(self):
        """
        Get all Roles for the current User

        Return all Roles for the User, grouping the local-Roles by the objects
        they are contextual to.
        """

        def role_names(roles):
            return list(sorted(r.__name__ for r in roles))

        orgs = [
            {"slug": m.org.slug, "roles": role_names(m.roles)}
            for m in self.org_memberships.all()
        ]

        projects = [
            {"slug": m.project.slug, "roles": role_names(m.roles)}
            for m in self.project_memberships.all()
        ]

        return {
            "global": role_names(self.roles),
            "orgs": orgs,
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

    @property
    def is_interactive_only(self):
        """
        Does this user only have access the Interactive part of the platform

        Because a user can have the InteractiveReporter role globally or via
        any project, along with other roles, we needed an easy way to identify
        when a user has only this role.
        """
        return self.all_roles == {InteractiveReporter}

    @property
    def name(self):
        """Unify the available names for a User."""
        return self.fullname or self.username

    def rotate_token(self):
        # ticket to look at signing request
        expires_at = timezone.now() + timedelta(days=90)

        # store as datetime in case we want to compare with a datetime or
        # increase resolution later.
        expires_at = expires_at.replace(hour=0, minute=0, second=0, microsecond=0)

        # suffix the token with the expiry date so it's clearer to users of it
        # when it will expire
        token = f"{secrets.token_hex(32)}-{expires_at.date().isoformat()}"

        # we're going to check the token against ones passed to the service,
        # but we don't want to expose ourselves to timing attacks.  So we're
        # storing it in the db as a hased string using Django's password
        # hashing tools and then comparing (in User.is_valid_pat()) with
        # secrets.compare_digest to avoid a timing attack there.
        hashed_token = hash_user_pat(token)

        self.pat_expires_at = expires_at
        self.pat_token = hashed_token
        self.save(update_fields=["pat_token", "pat_expires_at"])

        # return the unhashed token so it can be passed to a consuming service
        return token

    @cached_property
    def uses_social_auth(self):
        """
        Cache whether this user logs in via GitHub (using social auth)

        We use this in a couple of places in our base header template, so to
        avoid extra queries on every page load we're caching it to the user
        instance here.
        """
        return self.social_auth.exists()
