from datetime import UTC

import factory

from jobserver.models import (
    Release,
    ReleaseFile,
    ReleaseFileReview,
    Snapshot,
    SnapshotPublishRequest,
)


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

    mtime = factory.Faker("date_time", tzinfo=UTC)
    size = 7


class ReleaseFileReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReleaseFileReview

    created_by = factory.SubFactory("tests.factories.UserFactory")
    release_file = factory.SubFactory("tests.factories.ReleaseFileFactory")


class SnapshotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Snapshot

    created_by = factory.SubFactory("tests.factories.UserFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")


class SnapshotPublishRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SnapshotPublishRequest

    created_by = factory.SubFactory("tests.factories.UserFactory")
    snapshot = factory.SubFactory("tests.factories.SnapshotFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")
