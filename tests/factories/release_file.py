from datetime import UTC

import factory

from jobserver.models import ReleaseFile


class ReleaseFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReleaseFile

    created_by = factory.SubFactory("tests.factories.UserFactory")
    release = factory.SubFactory("tests.factories.ReleaseFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")

    mtime = factory.Faker("date_time", tzinfo=UTC)
    size = 7
