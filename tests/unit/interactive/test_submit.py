from interactive_templates.dates import (
    END_DATE,
    START_DATE,
)
from interactive_templates.schema import Codelist, v2

from interactive.submit import (
    submit_analysis,
)

from ...factories import (
    BackendFactory,
    ProjectFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_submit_analysis(remote_repo, add_codelist, slack_messages):
    add_codelist("org/slug-a", "codelist a")
    add_codelist("org/slug-b", "codelist b")
    backend = BackendFactory()
    project = ProjectFactory()
    repo = RepoFactory(url=str(remote_repo))
    WorkspaceFactory(project=project, repo=repo, name=f"{project.slug}-interactive")
    user = UserFactory()

    analysis = v2.Analysis(
        codelist_1=Codelist(label="", slug="org/slug-a", type=""),
        codelist_2=Codelist(label="", slug="org/slug-b", type=""),
        created_by=user.email,
        demographics=[],
        filter_population="all",
        repo=str(remote_repo),
        time_ever=False,
        time_scale="",
        time_value=1,
        start_date=START_DATE,
        end_date=END_DATE,
    )

    analysis_request = submit_analysis(
        analysis=analysis,
        backend=backend,
        creator=user,
        project=project,
        purpose="test",
        report_title="report title",
        title="analysis title",
    )

    assert analysis_request.created_by == user
    assert analysis_request.job_request
    assert analysis_request.project == project
    assert analysis_request.template_data["codelist_1"]["slug"] == "org/slug-a"
    assert analysis_request.template_data["codelist_2"]["slug"] == "org/slug-b"
    assert analysis_request.purpose == "test"
    assert analysis_request.report_title == "report title"
    assert analysis_request.title == "analysis title"

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert analysis_request.created_by.email in text
    assert analysis_request.job_request.get_absolute_url() in text
    assert analysis_request.job_request.sha in text
