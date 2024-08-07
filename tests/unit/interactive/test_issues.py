from interactive.issues import create_output_checking_request
from jobserver.first import first

from ...factories import AnalysisRequestFactory, JobRequestFactory


def test_create_output_checking_request(github_api):
    job_request = JobRequestFactory()
    AnalysisRequestFactory(job_request=job_request, purpose="important\n\nresearch")

    create_output_checking_request(job_request, github_api)

    lines = first(github_api.issues).body.split("\n")

    assert lines[0] == "### GitHub repo"
    assert lines[1] == job_request.workspace.repo.url

    assert lines[3] == "### Workspace"
    assert lines[4].endswith(job_request.workspace.get_absolute_url())

    assert lines[6] == "### Analysis request purpose"
    assert lines[7:10] == job_request.analysis_request.purpose.split("\n")
