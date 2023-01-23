from datetime import timezone

import factory

from jobserver.models import Release, ReleaseFile, ReleaseFileReview


class ReleaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Release

    backend = factory.SubFactory("tests.factories.BackendFactory")
    created_by = factory.SubFactory("tests.factories.UserFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")

    requested_files = []


class ReleaseFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReleaseFile

    created_by = factory.SubFactory("tests.factories.UserFactory")
    release = factory.SubFactory("tests.factories.ReleaseFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")

    mtime = factory.Faker("date_time", tzinfo=timezone.utc)
    size = 7


class ReleaseFileReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReleaseFileReview

    created_by = factory.SubFactory("tests.factories.UserFactory")
    release_file = factory.SubFactory("tests.factories.ReleaseFileFactory")
