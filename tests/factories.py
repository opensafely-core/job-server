import factory

from jobserver.models import Job, JobRequest, User, Workspace


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job


class JobRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobRequest

    created_by = factory.SubFactory("tests.factories.UserFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")


class WorkspaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workspace


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user-{n}")
    email = factory.Sequence(lambda n: f"user-{n}@example.com")
