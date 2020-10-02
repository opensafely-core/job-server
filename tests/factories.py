import factory

from jobserver.models import Job, User, Workspace


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job


class WorkspaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workspace


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
