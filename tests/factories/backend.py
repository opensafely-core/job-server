import factory

from jobserver.models import Backend


class BackendFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Backend

    slug = factory.Sequence(lambda n: f"backend-{n}")
    name = factory.Sequence(lambda n: f"Backend {n}")
    is_active = True
    rap_api_state = {}
