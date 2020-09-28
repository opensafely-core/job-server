import factory
from django.contrib.auth.models import User

from jobserver.models import Job


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
