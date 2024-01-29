import factory

from jobserver.models import Repo


class RepoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Repo

    url = factory.Sequence(lambda n: f"http://example.com/org-{n}/repo-{n}")
