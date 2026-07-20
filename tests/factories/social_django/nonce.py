import factory
from social_django.models import Nonce


class NonceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Nonce

    server_url = "https://example.com"
    timestamp = 1
    salt = "test_salt"
