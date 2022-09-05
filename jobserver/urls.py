import debug_toolbar
import social_django.views as social_django_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import RedirectView

from jobserver.api.jobs import (
    JobAPIUpdate,
    JobRequestAPIListCreate,
    UserAPIDetail,
    WorkspaceStatusesAPI,
)
from jobserver.api.releases import (
    ReleaseAPI,
    ReleaseFileAPI,
    ReleaseNotificationAPICreate,
    ReleaseWorkspaceAPI,
    ReviewAPI,
    SnapshotAPI,
    SnapshotCreateAPI,
    SnapshotPublishAPI,
    WorkspaceStatusAPI,
)

from .views.index import Index
from .views.job_requests import (
    JobRequestCancel,
    JobRequestCreate,
    JobRequestDetail,
    JobRequestDetailRedirect,
    JobRequestList,
    JobRequestPickRef,
)
from .views.jobs import JobCancel, JobDetail, JobDetailRedirect
from .views.orgs import OrgDetail, OrgList
from .views.projects import ProjectDetail
from .views.releases import (
    ProjectReleaseList,
    PublishedSnapshotFile,
    ReleaseDetail,
    ReleaseDownload,
    ReleaseFileDelete,
    SnapshotDetail,
    SnapshotDownload,
    WorkspaceReleaseList,
)
from .views.status import MaintenanceMode, PerBackendStatus, Status
from .views.users import Settings, login_view
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
    WorkspaceOutputsBadge,
)


api_urls = [
    path("job-requests/", JobRequestAPIListCreate.as_view()),
    path("jobs/", JobAPIUpdate.as_view()),
    path("release-notifications/", ReleaseNotificationAPICreate.as_view()),
    path("users/<str:username>/", UserAPIDetail.as_view(), name="user-detail"),
    path(
        "workspaces/<str:name>/statuses/",
        WorkspaceStatusesAPI.as_view(),
        name="workspace-statuses",
    ),
    # releasing outputs API
    path(
        "workspaces/<str:workspace_id>/snapshots",
        SnapshotCreateAPI.as_view(),
        name="snapshot-create",
    ),
    path(
        "workspaces/<workspace_id>/snapshots/<int:snapshot_id>",
        SnapshotAPI.as_view(),
        name="snapshot",
    ),
    path(
        "workspaces/<str:workspace_id>/snapshots/<int:snapshot_id>/publish",
        SnapshotPublishAPI.as_view(),
        name="snapshot-publish",
    ),
    path(
        "workspaces/<str:workspace_id>/status",
        WorkspaceStatusAPI.as_view(),
        name="workspace-status",
    ),
    path(
        "releases/workspace/<str:workspace_name>",
        ReleaseWorkspaceAPI.as_view(),
        name="release-workspace",
    ),
    path(
        "releases/release/<str:release_id>",
        ReleaseAPI.as_view(),
        name="release",
    ),
    path(
        "releases/release/<str:release_id>/reviews",
        ReviewAPI.as_view(),
        name="release-review",
    ),
    path(
        "releases/file/<file_id>",
        ReleaseFileAPI.as_view(),
        name="release-file",
    ),
]

files_urls = [
    path("", WorkspaceFileList.as_view(), name="workspace-files-list"),
    path(
        "<str:backend_slug>/",
        WorkspaceBackendFiles.as_view(),
        name="workspace-backend-files",
    ),
    path(
        "<str:backend_slug>/<path:path>",
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
    path("badge/", WorkspaceOutputsBadge.as_view(), name="workspace-outputs-badge"),
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

published_files_urls = [
    path("<file_id>/", PublishedSnapshotFile.as_view(), name="published-file"),
]

releases_urls = [
    path(
        "",
        WorkspaceReleaseList.as_view(),
        name="workspace-release-list",
    ),
    path("<str:pk>/", ReleaseDetail.as_view(), name="release-detail"),
    path("<str:pk>/download/", ReleaseDownload.as_view(), name="release-download"),
    path(
        "<str:pk>/<str:release_file_id>/delete/",
        ReleaseFileDelete.as_view(),
        name="release-file-delete",
    ),
    path("<str:pk>/<path:path>", ReleaseDetail.as_view(), name="release-detail"),
]

status_urls = [
    path("", Status.as_view(), name="status"),
    path("<slug:backend>/", PerBackendStatus.as_view(), name="status-backend"),
    path(
        "<slug:backend>/maintenance-mode/",
        MaintenanceMode.as_view(),
        name="status-maintenance-mode",
    ),
]

workspace_urls = [
    path(
        "",
        WorkspaceDetail.as_view(),
        name="workspace-detail",
    ),
    path(
        "run-jobs/",
        JobRequestCreate.as_view(),
        name="job-request-create",
    ),
    path(
        "run-jobs/<str:ref>/",
        JobRequestCreate.as_view(),
        name="job-request-create",
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
    path("pick-commit/", JobRequestPickRef.as_view(), name="job-request-pick-ref"),
    path("published/", include(published_files_urls)),
    path("releases/", include(releases_urls)),
    path("<int:pk>/", JobRequestDetail.as_view(), name="job-request-detail"),
    path("<int:pk>/cancel/", JobRequestCancel.as_view(), name="job-request-cancel"),
    path("<int:pk>/<identifier>/", JobDetail.as_view(), name="job-detail"),
    path("<int:pk>/<identifier>/cancel/", JobCancel.as_view(), name="job-cancel"),
]

project_urls = [
    path("", ProjectDetail.as_view(), name="project-detail"),
    path("new-workspace/", WorkspaceCreate.as_view(), name="workspace-create"),
    path("releases/", ProjectReleaseList.as_view(), name="project-release-list"),
    path("<str:workspace_slug>/", include(workspace_urls)),
]

urlpatterns = [
    path("", Index.as_view(), name="home"),
    path(
        "login/<str:backend>/",
        csrf_exempt(require_POST(social_django_views.auth)),
        name="auth-login",
    ),
    path("", include("social_django.urls", namespace="social")),
    path("", include("applications.urls")),
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico")),
    path("robots.txt", RedirectView.as_view(url=settings.STATIC_URL + "robots.txt")),
    path("api/v2/", include((api_urls, "api"))),
    path("event-log/", JobRequestList.as_view(), name="job-list"),
    path("event-list/", RedirectView.as_view(url="/event-log/")),
    path("jobs/", RedirectView.as_view(query_string=True, pattern_name="job-list")),
    path(
        "job-requests/<pk>/",
        JobRequestDetailRedirect.as_view(),
        name="job-request-detail",
    ),
    path("jobs/<identifier>/", JobDetailRedirect.as_view(), name="job-detail"),
    path("login/", login_view, name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("orgs/", OrgList.as_view(), name="org-list"),
    path("settings/", Settings.as_view(), name="settings"),
    path("staff/", include("staff.urls", namespace="staff")),
    path("status/", include(status_urls)),
    path("workspaces/", RedirectView.as_view(url="/")),
    path("__debug__/", include(debug_toolbar.urls)),
    path("__reload__/", include("django_browser_reload.urls")),
    path(
        "<str:org_slug>/",
        include(
            [
                path("", OrgDetail.as_view(), name="org-detail"),
                path(
                    "<str:project_slug>/",
                    include(project_urls),
                ),
            ]
        ),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
