import factory

from jobserver.models import Report, ReportPublishRequest


class ReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Report

    created_by = factory.SubFactory("tests.factories.UserFactory")
    release_file = factory.SubFactory("tests.factories.ReleaseFileFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")


class ReportPublishRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReportPublishRequest

    created_by = factory.SubFactory("tests.factories.UserFactory")
    release_file_publish_request = factory.SubFactory(
        "tests.factories.ReleaseFilePublishRequestFactory"
    )
    report = factory.SubFactory("tests.factories.ReportFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")
