import json
import tempfile

import pytest
from opensafely._vendor.jobrunner.cli import local_run

from interactive.submit import git
from interactive.views import AnalysisRequestCreate
from jobserver.authorization import InteractiveReporter

from ..factories import (
    BackendFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)
from ..fakes import FakeOpenCodelistsAPI


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
        "demographics": ["sex", "age"],
        "filterPopulation": "all",
        "timeScale": "years",
        "timeValue": "5",
    }
    request = rf.post("/", data=json.dumps(data), content_type="appliation/json")
    request.user = user

    response = AnalysisRequestCreate.as_view(
        get_opencodelists_api=AsthmaOpenCodelistsAPI
    )(request, org_slug=project.org.slug, project_slug=project.slug)

    # check the view redirects, a 200 means we have validation errors
    assert response.status_code == 302, response.context_data["form"].errors

    _, _, ar_pk = response.url.rpartition("/")

    # create a working directory to run the study in
    with tempfile.TemporaryDirectory(suffix=f"repo-{ar_pk}") as path:
        git("clone", repo.url, path)
        local_run.main(path, ["run_all"])
