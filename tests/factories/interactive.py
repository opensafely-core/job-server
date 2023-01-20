import factory

from interactive.dates import END_DATE, START_DATE
from interactive.models import AnalysisRequest


class AnalysisRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AnalysisRequest

    title = factory.Sequence(lambda n: f"Analysis Request {n}")
    slug = factory.Sequence(lambda n: f"analysis-request-{n}")
    start_date = START_DATE
    end_date = END_DATE
    codelist_name = "Asthma annual review QOF"
    codelist_slug = "opensafely/asthma-annual-review-qof"

    created_by = factory.SubFactory("tests.factories.UserFactory")
    job_request = factory.SubFactory("tests.factories.JobRequestFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
