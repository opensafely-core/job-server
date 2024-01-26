import factory

from jobserver.models import Snapshot


class SnapshotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Snapshot

    created_by = factory.SubFactory("tests.factories.UserFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")
