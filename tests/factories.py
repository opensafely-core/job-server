import factory
from django.contrib.auth.models import User

from jobserver.models import Job, Workspace


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job


class WorkspaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workspace


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
