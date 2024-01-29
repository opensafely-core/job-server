import factory

from jobserver.models import Backend


class BackendFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Backend

    slug = factory.Sequence(lambda n: f"backend-{n}")
    name = factory.Sequence(lambda n: f"Backend {n}")
    is_active = True
    level_4_url = factory.Sequence(lambda n: f"http://example.com/{n}")
    jobrunner_state = {}
