import factory

from jobserver.models import Report


class ReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Report

    created_by = factory.SubFactory("tests.factories.UserFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    release_file = factory.SubFactory("tests.factories.ReleaseFileFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")
