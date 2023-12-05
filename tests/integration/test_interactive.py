import json
import re
import tempfile
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from first import first
from interactive_templates import git

from interactive.models import AnalysisRequest
from interactive.views import AnalysisRequestCreate
from jobserver.authorization import CoreDeveloper, InteractiveReporter
from jobserver.models import PublishRequest
from jobserver.views.reports import PublishRequestCreate

from ..factories import (
    AnalysisRequestFactory,
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    RepoFactory,
    ReportFactory,
    UserFactory,
    WorkspaceFactory,
)
from ..fakes import FakeGitHubAPI, FakeOpenCodelistsAPI


@pytest.fixture
def local_repo():
    with tempfile.TemporaryDirectory() as path:
        git("init", "--bare", ".", "--initial-branch", "main", cwd=path)

        yield path


class AsthmaOpenCodelistsAPI(FakeOpenCodelistsAPI):
    def get_codelists(self, coding_system):
        return [
            {
                "slug": "opensafely/asthma-inhaler-salbutamol-medication/2020-04-15",
                "name": "Asthma Inhaler Salbutamol Medication",
                "organisation": "OpenSAFELY",
            },
            {
                "slug": "pincer/ast/v1.8",
                "name": "Asthma",
                "organisation": "PINCER",
            },
        ]


def assert_edit_and_publish_pages_are_locked(analysis, client):
    # check report metadata cannot be changed and new request cannot be made
    response = client.get(analysis.get_edit_url())
    assert response.status_code == 200
    assert "This report is currently locked" in response.rendered_content

    with patch.object(PublishRequestCreate, "get_github_api", FakeGitHubAPI):
        response = client.post(analysis.get_publish_url())
        assert response.status_code == 200
        assert (
            response.template_name == "interactive/publish_request_create_locked.html"
        )


@pytest.mark.slow_test
def test_interactive_submission_success(rf, local_repo, enable_network):
    BackendFactory(slug="tpp")
    project = ProjectFactory()
    repo = RepoFactory(url=local_repo)
    workspace = WorkspaceFactory(
        project=project, repo=repo, name=project.interactive_slug
    )

    assert workspace.is_interactive
    assert project.interactive_workspace

    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])

    # hit the submission view with form data
    data = {
        "title": "Asthma Inhaler Salbutamol Medication & Asthma",
        "codelistA": {
            "label": "Asthma Inhaler Salbutamol Medication",
            "organisation": "OpenSAFELY",
            "type": "medication",
            "value": "opensafely/asthma-inhaler-salbutamol-medication/2020-04-15",
        },
        "codelistB": {
            "label": "Asthma",
            "organisation": "PINCER",
            "type": "event",
            "value": "pincer/ast/v1.8",
        },
        "filterPopulation": "all",
        "purpose": "For… science!",
    }
    request = rf.post("/", data=json.dumps(data), content_type="appliation/json")
    request.user = user

    response = AnalysisRequestCreate.as_view(
        get_opencodelists_api=AsthmaOpenCodelistsAPI
    )(request, project_slug=project.slug)

    # check the view redirects, a 200 means we have validation errors
    assert response.status_code == 302, response.context_data["form"].errors

    ar_slug = response.url.rpartition("/")[0].rpartition("/")[-1]
    ar_pk = ar_slug.rpartition("-")[-1]
    analysis_request = AnalysisRequest.objects.get(slug=ar_slug)

    # Setting the Git SHA is done as a result of calling
    # interactive_template's create_commit function. This renders the analysis
    # code based on the contents of the template data. So if the template data
    # hasn't changed, all variables will be replaced in the project definition
    # and a commit will be made with the SHA saved to the job request.
    assert isinstance(analysis_request.job_request.sha, str)
    assert (
        f"generate_study_population_{ar_pk}"
        in analysis_request.job_request.project_definition
    )
    assert "{{" not in analysis_request.job_request.project_definition


def test_interactive_publishing_report_success(client, release, slack_messages):
    # set up the project…
    project = ProjectFactory()
    workspace = WorkspaceFactory(project=project, name=project.interactive_slug)

    # … and the user
    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])
    client.force_login(user)

    # "run" the job
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request, status="succeeded")

    report = ReportFactory(
        release_file=release.files.first(), project=project, title="My report title"
    )
    analysis = AnalysisRequestFactory(
        job_request=job_request, project=project, report=report
    )

    # this is a complex stack of factories so this is a little sense check to
    # ensure the analysis is in the expected success state to allow us to
    # request it's published
    assert analysis.status == "succeeded"

    # user can view their analysis page and the report is rendered there
    response = client.get(analysis.get_absolute_url())
    assert response.status_code == 200
    assert report.title in response.rendered_content

    # user creates a request to publish report
    with patch.object(PublishRequestCreate, "get_github_api", new=FakeGitHubAPI):
        response = client.post(analysis.get_publish_url(), follow=True)
        assert response.status_code == 200
        assert response.redirect_chain == [(analysis.get_absolute_url(), 302)]

    # check ticket is requested
    requests = PublishRequest.objects.filter(report=report)
    assert requests.count() == 1

    publish_request = requests.first()
    assert publish_request.created_by == user

    assert_edit_and_publish_pages_are_locked(analysis, client)

    staff = UserFactory(roles=[CoreDeveloper])
    client.force_login(staff)

    # check the staff area shows the pending publish request
    response = client.get(report.get_staff_url())
    assert response.status_code == 200
    assert "Publish requests" in response.rendered_content

    # parse out the Created by span (with the URL we care about) from the
    # rendered content.
    #
    # We have to find strings because calling find_all with an element name as
    # well as the regex doesn't give us any results.  We then have to filter
    # those down to get rid of the report creator.
    #
    # This is really painful.
    strings = BeautifulSoup(response.rendered_content, "html.parser").find_all(
        string=re.compile(".*Created by.*")
    )
    spans = [s.parent for s in strings]
    span = first(spans, key=lambda span: "on" in span.text)

    created_by_url = span.a["href"]
    assert created_by_url == user.get_staff_url()

    # staff approves request
    response = client.post(publish_request.get_approve_url(), follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(report.get_staff_url(), 302)]

    # check report and release file are now public
    assert release.files.first().snapshots.count() == 1
    assert release.files.first().snapshots.first().is_published
    assert report.is_published

    client.force_login(user)
    response = client.get(analysis.get_absolute_url())
    assert response.status_code == 200

    assert_edit_and_publish_pages_are_locked(analysis, client)

    # check the page can be viewed by a logged out user
    client.logout()
    response = client.get(analysis.get_absolute_url())
    assert response.status_code == 200
    assert report.title in response.rendered_content
