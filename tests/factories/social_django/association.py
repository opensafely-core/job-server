import factory
from social_django.models import Association


class AssociationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Association

    server_url = "https://example.com"
    handle = "test_handle"
    secret = "test_secret"
    issued = 1
    lifetime = 1
    assoc_type = "test_assoc_type"
