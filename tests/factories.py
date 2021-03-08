from datetime import datetime

import factory
import factory.fuzzy
from django.utils import timezone
from pytz import utc
from social_django.models import UserSocialAuth

from jobserver.models import (
    Backend,
    Job,
    JobRequest,
    Membership,
    Org,
    Project,
    Stats,
    User,
    Workspace,
    Release,
)


class BackendFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Backend

    name = factory.Sequence(lambda n: f"Backend {n}")


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job

    job_request = factory.SubFactory("tests.factories.JobRequestFactory")

    identifier = factory.Sequence(lambda n: f"identifier-{n}")

    updated_at = factory.fuzzy.FuzzyDateTime(datetime(2020, 1, 1, tzinfo=timezone.utc))


class JobRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobRequest

    backend = factory.SubFactory("tests.factories.BackendFactory")
    created_by = factory.SubFactory("tests.factories.UserFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")

    requested_actions = []


class MembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Membership

    project = factory.SubFactory("tests.factories.ProjectFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


class OrgFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Org

    name = factory.Sequence(lambda n: f"organisation-{n}")


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    org = factory.SubFactory("tests.factories.OrgFactory")

    name = factory.Sequence(lambda n: f"project-{n}")
    proposed_start_date = factory.fuzzy.FuzzyDateTime(
        datetime(2020, 1, 1, tzinfo=timezone.utc)
    )


class StatsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stats

    backend = factory.SubFactory("tests.factories.BackendFactory")

    api_last_seen = factory.Faker("date_time", tzinfo=utc)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user-{n}")
    email = factory.Sequence(lambda n: f"user-{n}@example.com")


class UserSocialAuthFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserSocialAuth

    user = factory.SubFactory("tests.factories.UserFactory")


class WorkspaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workspace

    name = factory.Sequence(lambda n: f"workspace-{n}")
    repo = factory.Sequence(lambda n: "http://example.com/org-{n}/repo-{n}")


class ReleaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Release

    backend = factory.SubFactory("tests.factories.BackendFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")
