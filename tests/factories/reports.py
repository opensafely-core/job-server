import factory

from jobserver.models import Report, ReportPublishRequest


class ReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Report

    created_by = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    release_file = factory.SubFactory("tests.factories.ReleaseFileFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")


class ReportPublishRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReportPublishRequest

    created_by = factory.SubFactory("tests.factories.UserFactory")
    report = factory.SubFactory("tests.factories.ReportFactory")
    snapshot_publish_request = factory.SubFactory(
        "tests.factories.SnapshotPublishRequestFactory"
    )
    updated_by = factory.SubFactory("tests.factories.UserFactory")
