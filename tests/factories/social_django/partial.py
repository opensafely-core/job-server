import factory
from social_django.models import Partial


class PartialFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Partial

    token = factory.Sequence(lambda n: f"token-{n}")
