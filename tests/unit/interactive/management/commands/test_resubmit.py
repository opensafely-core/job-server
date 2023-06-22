from django.core.management import call_command

from interactive.management.commands import resubmit_analysis as resubmit_analysis_cmd
from tests.factories import AnalysisRequestFactory, ProjectFactory, WorkspaceFactory
from tests.fakes import FakeGitHubAPI


def test_resubmit_analysis_success(monkeypatch):
    monkeypatch.setattr(resubmit_analysis_cmd, "_get_github_api", FakeGitHubAPI)

    project = ProjectFactory()
    analysis_request = AnalysisRequestFactory(project=project)
    WorkspaceFactory(name=project.interactive_slug, project=project)

    initial_id = analysis_request.job_request.id

    call_command("resubmit_analysis", analysis_request.id)
    analysis_request.refresh_from_db()

    assert analysis_request.job_request.id != initial_id
