import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from ....factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    OrgFactory,
    ProjectFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)
from ....utils import minutes_ago


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_workspace_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        WorkspaceFactory(**{field: None})


def test_workspace_constraints_published_at_and_published_by_both_set():
    WorkspaceFactory(signed_off_at=timezone.now(), signed_off_by=UserFactory())


def test_workspace_constraints_signed_off_at_and_signed_off_by_neither_set():
    WorkspaceFactory(signed_off_at=None, signed_off_by=None)


@pytest.mark.django_db(transaction=True)
def test_workspace_constraints_missing_signed_off_at_or_signed_off_by():
    with pytest.raises(IntegrityError):
        WorkspaceFactory(signed_off_at=None, signed_off_by=UserFactory())

    with pytest.raises(IntegrityError):
        WorkspaceFactory(signed_off_at=timezone.now(), signed_off_by=None)


def test_workspace_get_absolute_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    url = workspace.get_absolute_url()

    assert url == reverse(
        "workspace-detail",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_releases_api_url():
    workspace = WorkspaceFactory()
    assert (
        workspace.get_releases_api_url()
        == f"/api/v2/releases/workspace/{workspace.name}"
    )


def test_workspace_get_archive_toggle_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    url = workspace.get_archive_toggle_url()

    assert url == reverse(
        "workspace-archive-toggle",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_edit_url():
    workspace = WorkspaceFactory()

    url = workspace.get_edit_url()

    assert url == reverse(
        "workspace-edit",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_files_url():
    workspace = WorkspaceFactory()

    url = workspace.get_files_url()

    assert url == reverse(
        "workspace-files-list",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_jobs_url():
    workspace = WorkspaceFactory()

    url = workspace.get_jobs_url()

    assert url == reverse(
        "job-request-create",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_latest_outputs_download_url():
    workspace = WorkspaceFactory()

    url = workspace.get_latest_outputs_download_url()

    assert url == reverse(
        "workspace-latest-outputs-download",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_latest_outputs_url():
    workspace = WorkspaceFactory()

    url = workspace.get_latest_outputs_url()

    assert url == reverse(
        "workspace-latest-outputs-detail",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_logs_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    url = workspace.get_logs_url()

    assert url == reverse(
        "workspace-logs",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_notifications_toggle_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    url = workspace.get_notifications_toggle_url()

    assert url == reverse(
        "workspace-notifications-toggle",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_outputs_url():
    workspace = WorkspaceFactory()

    url = workspace.get_outputs_url()

    assert url == reverse(
        "workspace-output-list",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_pick_ref_url():
    workspace = WorkspaceFactory()

    url = workspace.get_pick_ref_url()

    assert url == reverse(
        "job-request-pick-ref",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_releases_url():
    workspace = WorkspaceFactory()

    url = workspace.get_releases_url()

    assert url == reverse(
        "workspace-release-list",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


def test_workspace_get_statuses_url():
    workspace = WorkspaceFactory()
    url = workspace.get_statuses_url()
    assert url == reverse("api:workspace-statuses", kwargs={"name": workspace.name})


def test_workspace_get_staff_url():
    workspace = WorkspaceFactory()

    url = workspace.get_staff_url()

    assert url == reverse("staff:workspace-detail", kwargs={"slug": workspace.name})


def test_workspace_get_staff_edit_url():
    workspace = WorkspaceFactory()

    url = workspace.get_staff_edit_url()

    assert url == reverse("staff:workspace-edit", kwargs={"slug": workspace.name})


def test_workspace_get_action_status_lut_no_jobs():
    assert WorkspaceFactory().get_action_status_lut() == {}


def test_workspace_get_action_status_lut_with_backend():
    workspace1 = WorkspaceFactory()
    job_request = JobRequestFactory(backend=BackendFactory(), workspace=workspace1)
    JobFactory(job_request=job_request, action="action1", status="pending")

    now = timezone.now()

    backend = BackendFactory()
    workspace2 = WorkspaceFactory()

    job_request1 = JobRequestFactory(backend=backend, workspace=workspace2)
    # action1 (succeeded) & action2 (failure)
    JobFactory(
        job_request=job_request1,
        action="action1",
        status="succeeded",
        created_at=minutes_ago(now, 7),
    )
    JobFactory(
        job_request=job_request1,
        action="action2",
        status="failed",
        created_at=minutes_ago(now, 6),
    )

    job_request2 = JobRequestFactory(backend=backend, workspace=workspace2)
    # action2 (succeeded) & action3 (failed)
    JobFactory(
        job_request=job_request2,
        action="action2",
        status="succeeded",
        created_at=minutes_ago(now, 5),
    )
    JobFactory(
        job_request=job_request2,
        action="action3",
        status="failed",
        created_at=minutes_ago(now, 4),
    )

    job_request3 = JobRequestFactory(backend=backend, workspace=workspace2)
    # action2 (failed)
    JobFactory(
        job_request=job_request3,
        action="action2",
        status="failed",
        created_at=minutes_ago(now, 2),
    )

    job_request4 = JobRequestFactory(backend=backend, workspace=workspace2)
    # action3 (succeeded) & action4 (failed)
    JobFactory(
        job_request=job_request4,
        action="action3",
        status="succeeded",
        created_at=minutes_ago(now, 2),
    )
    JobFactory(
        job_request=job_request4,
        action="action4",
        status="failed",
        created_at=minutes_ago(now, 1),
    )

    output = workspace2.get_action_status_lut(backend=backend.slug)
    expected = {
        "action1": "succeeded",
        "action2": "failed",
        "action3": "succeeded",
        "action4": "failed",
    }
    assert output == expected


def test_workspace_get_action_status_lut_without_backend():
    workspace1 = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace1)
    JobFactory(job_request=job_request, action="action1", status="pending")

    now = timezone.now()

    workspace2 = WorkspaceFactory()

    job_request1 = JobRequestFactory(workspace=workspace2)
    # action1 (succeeded) & action2 (failure)
    JobFactory(
        job_request=job_request1,
        action="action1",
        status="succeeded",
        created_at=minutes_ago(now, 7),
    )
    JobFactory(
        job_request=job_request1,
        action="action2",
        status="failed",
        created_at=minutes_ago(now, 6),
    )

    job_request2 = JobRequestFactory(workspace=workspace2)
    # action2 (succeeded) & action3 (failed)
    JobFactory(
        job_request=job_request2,
        action="action2",
        status="succeeded",
        created_at=minutes_ago(now, 5),
    )
    JobFactory(
        job_request=job_request2,
        action="action3",
        status="failed",
        created_at=minutes_ago(now, 4),
    )

    job_request3 = JobRequestFactory(workspace=workspace2)
    # action2 (failed)
    JobFactory(
        job_request=job_request3,
        action="action2",
        status="failed",
        created_at=minutes_ago(now, 2),
    )

    job_request4 = JobRequestFactory(workspace=workspace2)
    # action3 (succeeded) & action4 (failed)
    JobFactory(
        job_request=job_request4,
        action="action3",
        status="succeeded",
        created_at=minutes_ago(now, 2),
    )
    JobFactory(
        job_request=job_request4,
        action="action4",
        status="failed",
        created_at=minutes_ago(now, 1),
    )

    output = workspace2.get_action_status_lut()
    expected = {
        "action1": "succeeded",
        "action2": "failed",
        "action3": "succeeded",
        "action4": "failed",
    }
    assert output == expected


def test_workspace_is_interactive():
    assert WorkspaceFactory(name="test-interactive").is_interactive
    assert not WorkspaceFactory().is_interactive


def test_workspace_str():
    repo = RepoFactory(url="Corellia")
    workspace = WorkspaceFactory(name="Corellian Engineering Corporation", repo=repo)
    assert str(workspace) == "Corellian Engineering Corporation (Corellia)"
