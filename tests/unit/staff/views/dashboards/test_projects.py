from datetime import datetime, timezone

import pytest
from django.core.exceptions import PermissionDenied

from staff.views.dashboards.projects import ProjectsDashboard

from .....factories import (
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
    ReleaseFactory,
    ReleaseFileFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_projects_success(rf, core_developer):
    project = ProjectFactory()
    workspace = WorkspaceFactory(project=project)
    release = ReleaseFactory(workspace=workspace)
    ReleaseFileFactory.create_batch(15, release=release, workspace=workspace)

    job_request1 = JobRequestFactory(workspace=workspace)
    JobFactory(
        job_request=job_request1, started_at=datetime(2020, 7, 31, tzinfo=timezone.utc)
    )
    job_request2 = JobRequestFactory(workspace=workspace)
    JobFactory(
        job_request=job_request2, started_at=datetime(2021, 9, 3, tzinfo=timezone.utc)
    )

    request = rf.get("/")
    request.user = core_developer

    response = ProjectsDashboard.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["projects"]) == 1

    project = response.context_data["projects"][0]
    assert project["date_first_run"] == datetime(
        2020, 7, 31, 0, 0, 0, tzinfo=timezone.utc
    )
    assert project["files_released_count"] == 15
    assert project["job_request_count"] == 2
    assert project["workspace_count"] == 1


def test_projects_unauthorized(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectsDashboard.as_view()(request)
