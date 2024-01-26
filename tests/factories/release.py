import factory

from jobserver.models import Release


class ReleaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Release

    backend = factory.SubFactory("tests.factories.BackendFactory")
    created_by = factory.SubFactory("tests.factories.UserFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")

    requested_files = []
