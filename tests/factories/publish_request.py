import factory

from jobserver.models import PublishRequest


class PublishRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PublishRequest

    created_by = factory.SubFactory("tests.factories.UserFactory")
    snapshot = factory.SubFactory("tests.factories.SnapshotFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")
