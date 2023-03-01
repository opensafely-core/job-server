import inspect

import pytest
from django.contrib.auth.views import LogoutView
from django.urls import resolve
from django.views.generic import TemplateView
from social_django.views import auth as social_django_auth_view

from applications import views as applications
from jobserver.api.jobs import (
    JobAPIUpdate,
    JobRequestAPIList,
    UserAPIDetail,
    WorkspaceStatusesAPI,
)
from jobserver.api.releases import (
    ReleaseAPI,
    ReleaseFileAPI,
    ReleaseNotificationAPICreate,
    ReleaseWorkspaceAPI,
    SnapshotAPI,
    SnapshotCreateAPI,
    SnapshotPublishAPI,
    WorkspaceStatusAPI,
)
from jobserver.utils import dotted_path
from jobserver.views import (
    index,
    job_requests,
    jobs,
    orgs,
    projects,
    releases,
    status,
    users,
    workspaces,
)
from staff.views import applications as staff_applications
from staff.views import backends as staff_backends
from staff.views import orgs as staff_orgs
from staff.views import projects as staff_projects
from staff.views import redirects as staff_redirects
from staff.views import users as staff_users
from staff.views import workspaces as staff_workspaces


@pytest.mark.parametrize(
    "url,redirect",
    [
        ("/applications/42/", "/applications/42/page/contact-details/"),
        ("/applications/42/researchers/", "/applications/42/researchers/add/"),
        ("/favicon.ico", "/static/favicon.ico"),
        ("/event-list/", "/event-log/"),
        ("/jobs/", "/event-log/"),
        ("/workspaces/", "/"),
    ],
)
def test_url_redirects(client, url, redirect):
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == redirect


@pytest.mark.parametrize(
    "url,view",
    [
        ("/", index.Index),
        ("/api/v2/job-requests/", JobRequestAPIList),
        ("/api/v2/jobs/", JobAPIUpdate),
        ("/api/v2/release-notifications/", ReleaseNotificationAPICreate),
        ("/api/v2/users/ben/", UserAPIDetail),
        ("/api/v2/workspaces/w/statuses/", WorkspaceStatusesAPI),
        ("/api/v2/workspaces/w/snapshots", SnapshotCreateAPI),
        ("/api/v2/workspaces/w/snapshots/42", SnapshotAPI),
        ("/api/v2/workspaces/w/snapshots/42/publish", SnapshotPublishAPI),
        ("/api/v2/workspaces/w/status", WorkspaceStatusAPI),
        ("/api/v2/releases/workspace/w", ReleaseWorkspaceAPI),
        ("/api/v2/releases/release/42", ReleaseAPI),
        ("/api/v2/releases/file/42", ReleaseFileAPI),
        ("/apply/", TemplateView),
        ("/apply/sign-in", applications.sign_in),
        ("/apply/terms/", applications.terms),
        ("/applications/", applications.ApplicationList),
        ("/applications/42/page/42/", applications.page),
        ("/applications/42/confirmation/", applications.Confirmation),
        ("/applications/42/delete/", applications.ApplicationRemove),
        ("/applications/42/restore/", applications.ApplicationRestore),
        ("/applications/42/researchers/add/", applications.ResearcherCreate),
        ("/applications/42/researchers/42/delete/", applications.ResearcherDelete),
        ("/applications/42/researchers/42/edit/", applications.ResearcherEdit),
        ("/event-log/", job_requests.JobRequestList),
        ("/staff/applications/", staff_applications.ApplicationList),
        ("/staff/applications/42/", staff_applications.ApplicationDetail),
        ("/staff/applications/42/approve/", staff_applications.ApplicationApprove),
        ("/staff/applications/42/edit/", staff_applications.ApplicationEdit),
        ("/staff/applications/42/delete/", staff_applications.ApplicationRemove),
        ("/staff/applications/42/restore/", staff_applications.ApplicationRestore),
        ("/staff/backends/", staff_backends.BackendList),
        ("/staff/backends/42/", staff_backends.BackendDetail),
        ("/staff/backends/42/edit/", staff_backends.BackendEdit),
        ("/staff/backends/42/rotate-token/", staff_backends.BackendRotateToken),
        ("/staff/orgs/add/", staff_orgs.OrgCreate),
        ("/staff/orgs/o/add-github-org/", staff_orgs.org_add_github_org),
        ("/staff/orgs/o/remove-github-org/", staff_orgs.OrgRemoveGitHubOrg),
        ("/staff/projects/", staff_projects.ProjectList),
        ("/staff/projects/p/", staff_projects.ProjectDetail),
        ("/staff/projects/p/edit/", staff_projects.ProjectEdit),
        ("/staff/projects/p/feature-flags/", staff_projects.ProjectFeatureFlags),
        ("/staff/redirects/", staff_redirects.RedirectList),
        ("/staff/redirects/42/", staff_redirects.RedirectDetail),
        ("/staff/users/", staff_users.UserList),
        ("/staff/users/<username>/", staff_users.UserDetail),
        ("/staff/workspaces/", staff_workspaces.WorkspaceList),
        ("/staff/workspaces/w/", staff_workspaces.WorkspaceDetail),
        ("/job-requests/42/", job_requests.JobRequestDetailRedirect),
        ("/jobs/<identifier>/", jobs.JobDetailRedirect),
        ("/login/github/", social_django_auth_view),
        ("/logout/", LogoutView),
        ("/orgs/", orgs.OrgList),
        ("/settings/", users.Settings),
        ("/status/", status.Status),
        ("/o/", orgs.OrgDetail),
        ("/o/p/", projects.ProjectDetail),
        ("/o/p/new-workspace/", workspaces.WorkspaceCreate),
        ("/o/p/releases/", releases.ProjectReleaseList),
        ("/o/p/w/", workspaces.WorkspaceDetail),
        ("/o/p/w/run-jobs/", job_requests.JobRequestCreate),
        ("/o/p/w/archive-toggle/", workspaces.WorkspaceArchiveToggle),
        ("/o/p/w/files/", workspaces.WorkspaceFileList),
        ("/o/p/w/files/tpp/", workspaces.WorkspaceBackendFiles),
        ("/o/p/w/files/tpp/file.txt", workspaces.WorkspaceBackendFiles),
        ("/o/p/w/logs/", workspaces.WorkspaceLog),
        ("/o/p/w/notifications-toggle/", workspaces.WorkspaceNotificationsToggle),
        ("/o/p/w/outputs/", workspaces.WorkspaceOutputList),
        ("/o/p/w/outputs/latest/", workspaces.WorkspaceLatestOutputsDetail),
        ("/o/p/w/outputs/latest/download/", workspaces.WorkspaceLatestOutputsDownload),
        ("/o/p/w/outputs/latest/file.txt", workspaces.WorkspaceLatestOutputsDetail),
        ("/o/p/w/outputs/42/", releases.SnapshotDetail),
        ("/o/p/w/outputs/42/download/", releases.SnapshotDownload),
        ("/o/p/w/outputs/42/file.txt", releases.SnapshotDetail),
        ("/o/p/w/published/42/", releases.PublishedSnapshotFile),
        ("/o/p/w/releases/", releases.WorkspaceReleaseList),
        ("/o/p/w/releases/42/", releases.ReleaseDetail),
        ("/o/p/w/releases/42/download/", releases.ReleaseDownload),
        ("/o/p/w/releases/42/abc/delete/", releases.ReleaseFileDelete),
        ("/o/p/w/releases/42/file.txt", releases.ReleaseDetail),
        ("/o/p/w/42/", job_requests.JobRequestDetail),
        ("/o/p/w/42/cancel/", job_requests.JobRequestCancel),
        ("/o/p/w/42/abc/", jobs.JobDetail),
        ("/o/p/w/42/abc/cancel/", jobs.JobCancel),
    ],
)
def test_url_resolution(url, view):
    """Test each URL resolves to the expected view function or class"""
    match = resolve(url)

    # get the actual class for a CBV.  View.as_view() constructs a new wrapper
    # function to be the callable which url resolution calls when a view is
    # accessed.  We don't want that callable at this point in the test because
    # we're just checking configuration.
    if hasattr(match.func, "view_class"):
        resolved_view = match.func.view_class
    else:
        resolved_view = match.func
    assert dotted_path(resolved_view) == dotted_path(view), url

    msg = f"Resolved view '{match.func}' is a class. Did you forget `.as_view()`?"
    assert not inspect.isclass(match.func), msg
