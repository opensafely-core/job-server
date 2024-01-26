import factory

from jobserver.models import Org


class OrgFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Org

    name = factory.Sequence(lambda n: f"Organisation {n}")
    slug = factory.Sequence(lambda n: f"organisation-{n}")
