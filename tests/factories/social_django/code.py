import factory
from social_django.models import Code


class CodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Code

    email = "person@example.com"
    code = "test_code"
