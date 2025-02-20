import re
from unittest.mock import patch

from bs4 import BeautifulSoup

from jobserver.authorization import (
    InteractiveReporter,
    StaffAreaAdministrator,
)
from jobserver.models import PublishRequest
from jobserver.views.reports import PublishRequestCreate

from ..factories import (
    AnalysisRequestFactory,
    JobFactory,
    JobRequestFactory,
    OrgFactory,
    ProjectFactory,
    ReportFactory,
    UserFactory,
    WorkspaceFactory,
)
from ..fakes import FakeGitHubAPI


def assert_publish_page_is_locked(analysis, client):
    with patch.object(PublishRequestCreate, "get_github_api", FakeGitHubAPI):
        response = client.post(analysis.get_publish_url())
        assert response.status_code == 200
        assert (
            response.template_name == "interactive/publish_request_create_locked.html"
        )


def test_interactive_publishing_report_success(
    client, project_membership, release, slack_messages
):
    # set up the project…
    project = ProjectFactory(org=OrgFactory())
    workspace = WorkspaceFactory(project=project, name=project.interactive_slug)

    # … and the user
    user = UserFactory()
    project_membership(project=project, user=user, roles=[InteractiveReporter])
    client.force_login(user)

    # "run" the job
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request, status="succeeded")

    # The release fixture (eventually) creates an instance of Workspace. However, this
    # instance is different to the instance that is created by WorkspaceFactory.
    # This is a problem, because we need a workspace such that workspace.project.org
    # points to an Org; it doesn't by the release fixture route, but it does by the
    # WorkspaceFactory route. To fix the problem, we take the unusual step of switching
    # the workspace.
    release_file = release.files.first()
    release_file.workspace = workspace
    release_file.save()

    report = ReportFactory(
        release_file=release_file, project=project, title="My report title"
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

    assert_publish_page_is_locked(analysis, client)

    staff = UserFactory(roles=[StaffAreaAdministrator])
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
    span = next(sp for sp in spans if "on" in sp.text)  # pragma: no branch

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

    assert_publish_page_is_locked(analysis, client)

    # check the page can be viewed by a logged out user
    client.logout()
    response = client.get(analysis.get_absolute_url())
    assert response.status_code == 200
    assert report.title in response.rendered_content
