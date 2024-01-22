from datetime import UTC, datetime

import factory
import factory.fuzzy
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from social_django.models import Partial, UserSocialAuth

from jobserver.models import (
    AuditableEvent,
    Backend,
    BackendMembership,
    Job,
    JobRequest,
    Org,
    OrgMembership,
    Project,
    ProjectCollaboration,
    Repo,
    Stats,
    User,
    Workspace,
)


def generate_traceparent():
    """Generate an OTel trace context, as would be passed up from job-runner."""
    ctx = {}
    tracer = trace.get_tracer("jobs")
    root = tracer.start_span("JOB")

    with trace.use_span(root, end_on_exit=False):
        TraceContextTextMapPropagator().inject(ctx)

    return ctx


class AuditableEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuditableEvent


class BackendFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Backend

    slug = factory.Sequence(lambda n: f"backend-{n}")
    name = factory.Sequence(lambda n: f"Backend {n}")
    is_active = True
    level_4_url = factory.Sequence(lambda n: f"http://example.com/{n}")
    jobrunner_state = {}


class BackendMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BackendMembership

    backend = factory.SubFactory("tests.factories.BackendFactory")
    user = factory.SubFactory("tests.factories.UserFactory")

    created_by = factory.SubFactory("tests.factories.UserFactory")


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job

    job_request = factory.SubFactory("tests.factories.JobRequestFactory")

    identifier = factory.Sequence(lambda n: f"identifier-{n}")

    updated_at = factory.fuzzy.FuzzyDateTime(datetime(2020, 1, 1, tzinfo=UTC))

    trace_context = factory.LazyFunction(generate_traceparent)


class JobRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobRequest

    backend = factory.SubFactory("tests.factories.BackendFactory")
    created_by = factory.SubFactory("tests.factories.UserFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")

    requested_actions = []


class OrgFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Org

    name = factory.Sequence(lambda n: f"Organisation {n}")
    slug = factory.Sequence(lambda n: f"organisation-{n}")


class OrgMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrgMembership

    org = factory.SubFactory("tests.factories.OrgFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project
        skip_postgeneration_save = True

    created_by = factory.SubFactory("tests.factories.UserFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")

    name = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.Sequence(lambda n: f"project-{n}")

    @factory.post_generation
    def orgs(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, or nothing to add, do nothing.
            return

        # Add the iterable of groups using bulk addition
        for org in extracted:
            ProjectCollaborationFactory(org=org, project=self, is_lead=True)


class ProjectCollaborationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectCollaboration

    created_by = factory.SubFactory("tests.factories.UserFactory")
    org = factory.SubFactory("tests.factories.OrgFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")


class RepoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Repo

    url = factory.Sequence(lambda n: f"http://example.com/org-{n}/repo-{n}")


class StatsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stats

    backend = factory.SubFactory("tests.factories.BackendFactory")

    api_last_seen = factory.Faker("date_time", tzinfo=UTC)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user-{n}")
    email = factory.Sequence(lambda n: f"user-{n}@example.com")


class UserSocialAuthFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserSocialAuth

    provider = "github"
    uid = factory.Sequence(lambda n: f"uid-{n}")
    user = factory.SubFactory("tests.factories.UserFactory")


class WorkspaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workspace

    project = factory.SubFactory("tests.factories.ProjectFactory")
    repo = factory.SubFactory("tests.factories.RepoFactory")
    created_by = factory.SubFactory("tests.factories.UserFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")

    name = factory.Sequence(lambda n: f"workspace-{n}")


class PartialFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Partial

    token = factory.Sequence(lambda n: f"token-{n}")
