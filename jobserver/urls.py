import debug_toolbar
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.generic import RedirectView

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

from .views.admin import ApproveUsers
from .views.backends import BackendDetail, BackendEdit, BackendList, BackendRotateToken
from .views.index import Index
from .views.job_requests import JobRequestCancel, JobRequestDetail, JobRequestList
from .views.jobs import JobCancel, JobDetail
from .views.orgs import OrgCreate, OrgDetail, OrgList
from .views.projects import (
    ProjectAcceptInvite,
    ProjectCancelInvite,
    ProjectCreate,
    ProjectDetail,
    ProjectEdit,
    ProjectInvitationCreate,
    ProjectMembershipEdit,
    ProjectMembershipRemove,
    ProjectOnboardingCreate,
    ProjectSettings,
)
from .views.releases import (
    ProjectReleaseList,
    ReleaseDetail,
    ReleaseDownload,
    ReleaseFileDelete,
    SnapshotDetail,
    SnapshotDownload,
    WorkspaceReleaseList,
)
from .views.status import Status
from .views.users import Settings, UserDetail, UserList
from .views.workspaces import (
    WorkspaceArchiveToggle,
    WorkspaceBackendFiles,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceFileList,
    WorkspaceLatestOutputsDetail,
    WorkspaceLatestOutputsDownload,
    WorkspaceLog,
    WorkspaceNotificationsToggle,
    WorkspaceOutputList,
)


api_urls = [
    path("job-requests/", JobRequestAPIList.as_view()),
    path("jobs/", JobAPIUpdate.as_view()),
    path("release-notifications/", ReleaseNotificationAPICreate.as_view()),
    path("users/<username>/", UserAPIDetail.as_view(), name="user-detail"),
    path(
        "workspaces/<name>/statuses/",
        WorkspaceStatusesAPI.as_view(),
        name="workspace-statuses",
    ),
    # releasing outputs API
    path(
        "workspaces/<workspace_id>/snapshots",
        SnapshotCreateAPI.as_view(),
        name="snapshot-create",
    ),
    path(
        "workspaces/<workspace_id>/snapshots/<snapshot_id>",
        SnapshotAPI.as_view(),
        name="snapshot",
    ),
    path(
        "workspaces/<workspace_id>/snapshots/<snapshot_id>/publish",
        SnapshotPublishAPI.as_view(),
        name="snapshot-publish",
    ),
    path(
        "workspaces/<workspace_id>/status",
        WorkspaceStatusAPI.as_view(),
        name="workspace-status",
    ),
    path(
        "releases/workspace/<workspace_name>",
        ReleaseWorkspaceAPI.as_view(),
        name="release-workspace",
    ),
    path(
        "releases/release/<release_id>",
        ReleaseAPI.as_view(),
        name="release",
    ),
    path(
        "releases/file/<file_id>",
        ReleaseFileAPI.as_view(),
        name="release-file",
    ),
]

backend_urls = [
    path("", BackendList.as_view(), name="backend-list"),
    path("<int:pk>/", BackendDetail.as_view(), name="backend-detail"),
    path("<int:pk>/edit/", BackendEdit.as_view(), name="backend-edit"),
    path(
        "<int:pk>/rotate-token/",
        BackendRotateToken.as_view(),
        name="backend-rotate-token",
    ),
]

files_urls = [
    path("", WorkspaceFileList.as_view(), name="workspace-files-list"),
    path(
        "<backend_slug>/",
        WorkspaceBackendFiles.as_view(),
        name="workspace-backend-files",
    ),
    path(
        "<backend_slug>/<path:path>",
        WorkspaceBackendFiles.as_view(),
        name="workspace-backend-files",
    ),
]

outputs_urls = [
    path("", WorkspaceOutputList.as_view(), name="workspace-output-list"),
    path(
        "latest/",
        WorkspaceLatestOutputsDetail.as_view(),
        name="workspace-latest-outputs-detail",
    ),
    path(
        "latest/download/",
        WorkspaceLatestOutputsDownload.as_view(),
        name="workspace-latest-outputs-download",
    ),
    path(
        "latest/<path:path>",
        WorkspaceLatestOutputsDetail.as_view(),
        name="workspace-latest-outputs-detail",
    ),
    path(
        "<int:pk>/",
        SnapshotDetail.as_view(),
        name="workspace-snapshot-detail",
    ),
    path(
        "<int:pk>/download/",
        SnapshotDownload.as_view(),
        name="workspace-snapshot-download",
    ),
    path(
        "<int:pk>/<path:path>",
        SnapshotDetail.as_view(),
        name="workspace-snapshot-detail",
    ),
]

releases_urls = [
    path(
        "",
        WorkspaceReleaseList.as_view(),
        name="workspace-release-list",
    ),
    path("<pk>/", ReleaseDetail.as_view(), name="release-detail"),
    path("<pk>/download/", ReleaseDownload.as_view(), name="release-download"),
    path(
        "<pk>/<release_file_id>/delete/",
        ReleaseFileDelete.as_view(),
        name="release-file-delete",
    ),
    path("<pk>/<path:path>", ReleaseDetail.as_view(), name="release-detail"),
]

workspace_urls = [
    path(
        "",
        WorkspaceDetail.as_view(),
        name="workspace-detail",
    ),
    path(
        "archive-toggle/",
        WorkspaceArchiveToggle.as_view(),
        name="workspace-archive-toggle",
    ),
    path("files/", include(files_urls)),
    path("logs/", WorkspaceLog.as_view(), name="workspace-logs"),
    path(
        "notifications-toggle/",
        WorkspaceNotificationsToggle.as_view(),
        name="workspace-notifications-toggle",
    ),
    path("outputs/", include(outputs_urls)),
    path("releases/", include(releases_urls)),
]

project_urls = [
    path("", ProjectDetail.as_view(), name="project-detail"),
    path(
        "accept-invite/<signed_pk>/",
        ProjectAcceptInvite.as_view(),
        name="project-accept-invite",
    ),
    path("cancel-invite/", ProjectCancelInvite.as_view(), name="project-cancel-invite"),
    path("edit/", ProjectEdit.as_view(), name="project-edit"),
    path(
        "invite-users/",
        ProjectInvitationCreate.as_view(),
        name="project-invitation-create",
    ),
    path(
        "members/<int:pk>/edit",
        ProjectMembershipEdit.as_view(),
        name="project-membership-edit",
    ),
    path(
        "members/<int:pk>/remove",
        ProjectMembershipRemove.as_view(),
        name="project-membership-remove",
    ),
    path("new-workspace/", WorkspaceCreate.as_view(), name="workspace-create"),
    path("releases/", ProjectReleaseList.as_view(), name="project-release-list"),
    path("settings/", ProjectSettings.as_view(), name="project-settings"),
    path("<workspace_slug>/", include(workspace_urls)),
]

org_urls = [
    path("", OrgList.as_view(), name="org-list"),
    path("new/", OrgCreate.as_view(), name="org-create"),
]

user_urls = [
    path("", UserList.as_view(), name="user-list"),
    path("<username>/", UserDetail.as_view(), name="user-detail"),
]

urlpatterns = [
    path("", Index.as_view()),
    path("", include("social_django.urls", namespace="social")),
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico")),
    path("admin/approve-users", ApproveUsers.as_view(), name="approve-users"),
    path("admin/", admin.site.urls),
    path("api/v2/", include((api_urls, "api"))),
    path("backends/", include(backend_urls)),
    path("jobs/", JobRequestList.as_view(), name="job-list"),
    path("job-requests/", RedirectView.as_view(pattern_name="job-list")),
    path(
        "job-requests/<int:pk>/", JobRequestDetail.as_view(), name="job-request-detail"
    ),
    path(
        "job-requests/<int:pk>/cancel/",
        JobRequestCancel.as_view(),
        name="job-request-cancel",
    ),
    path("jobs/<identifier>/", JobDetail.as_view(), name="job-detail"),
    path("jobs/<identifier>/cancel/", JobCancel.as_view(), name="job-cancel"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("orgs/", include(org_urls)),
    path("settings/", Settings.as_view(), name="settings"),
    path("status/", Status.as_view(), name="status"),
    path("users/", include(user_urls)),
    path("workspaces/", RedirectView.as_view(url="/")),
    path("__debug__/", include(debug_toolbar.urls)),
    path(
        "<org_slug>/",
        include(
            [
                path("", OrgDetail.as_view(), name="org-detail"),
                path(
                    "new-project/",
                    ProjectCreate.as_view(),
                    name="project-create",
                ),
                path(
                    "project-onboarding/",
                    ProjectOnboardingCreate.as_view(),
                    name="project-onboarding",
                ),
                path(
                    "<project_slug>/",
                    include(project_urls),
                ),
            ]
        ),
    ),
]
