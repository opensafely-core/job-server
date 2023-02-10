import factory

from interactive.models import AnalysisRequest


class AnalysisRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AnalysisRequest

    title = factory.Sequence(lambda n: f"Analysis Request {n}")
    slug = factory.Sequence(lambda n: f"analysis-request-{n}")

    created_by = factory.SubFactory("tests.factories.UserFactory")
    job_request = factory.SubFactory("tests.factories.JobRequestFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
