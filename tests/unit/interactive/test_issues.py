from interactive.issues import create_output_checking_request

from ...factories import AnalysisRequestFactory, JobRequestFactory


def test_create_output_checking_request():
    job_request = JobRequestFactory()
    AnalysisRequestFactory(job_request=job_request, purpose="important\n\nresearch")

    class CapturingAPI:
        def create_issue(self, org, repo, title, body, labels):
            # capture all the values so they can interrogated later
            self.org = org
            self.repo = repo
            self.title = title
            self.body = body
            self.labels = labels

    issue = CapturingAPI()

    create_output_checking_request(job_request, issue)

    lines = issue.body.split("\n")

    assert lines[0] == "### GitHub repo"
    assert lines[1] == job_request.workspace.repo.url

    assert lines[3] == "### Workspace"
    assert lines[4].endswith(job_request.workspace.get_absolute_url())

    assert lines[6] == "### Analysis request purpose"
    assert lines[7:10] == job_request.analysis_request.purpose.split("\n")
