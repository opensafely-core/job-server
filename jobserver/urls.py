"""jobserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.generic import RedirectView

from .api import (
    JobAPIUpdate,
    JobRequestAPIList,
    ReleaseUploadAPI,
    UserAPIDetail,
    WorkspaceStatusesAPI,
)
from .views import (
    BackendDetail,
    BackendList,
    BackendRotateToken,
    Index,
    JobCancel,
    JobDetail,
    JobRequestCancel,
    JobRequestDetail,
    JobRequestList,
    JobRequestZombify,
    JobZombify,
    OrgCreate,
    OrgDetail,
    OrgList,
    ProjectCreate,
    ProjectDetail,
    Settings,
    Status,
    WorkspaceArchiveToggle,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceLog,
    WorkspaceNotificationsToggle,
    WorkspaceReleaseView,
)


api_urls = [
    path("job-requests/", JobRequestAPIList.as_view()),
    path("jobs/", JobAPIUpdate.as_view()),
    path("users/<username>/", UserAPIDetail.as_view(), name="user-detail"),
    path(
        "workspaces/<name>/statuses/",
        WorkspaceStatusesAPI.as_view(),
        name="workspace-statuses",
    ),
    path(
        "workspaces/<workspace_name>/releases/<release_hash>",
        ReleaseUploadAPI.as_view(),
        name="workspace-upload-release",
    ),
]

urlpatterns = [
    path("", Index.as_view()),
    path("", include("social_django.urls", namespace="social")),
    path("admin/", admin.site.urls),
    path("api/v2/", include(api_urls)),
    path("backends/", BackendList.as_view(), name="backend-list"),
    path("backends/<pk>/", BackendDetail.as_view(), name="backend-detail"),
    path(
        "backends/<pk>/rotate-token/",
        BackendRotateToken.as_view(),
        name="backend-rotate-token",
    ),
    path("jobs/", JobRequestList.as_view(), name="job-list"),
    path("job-requests/", RedirectView.as_view(pattern_name="job-list")),
    path("job-requests/<pk>/", JobRequestDetail.as_view(), name="job-request-detail"),
    path(
        "job-requests/<pk>/cancel/",
        JobRequestCancel.as_view(),
        name="job-request-cancel",
    ),
    path(
        "job-requests/<pk>/zombify/",
        JobRequestZombify.as_view(),
        name="job-request-zombify",
    ),
    path("jobs/<identifier>/", JobDetail.as_view(), name="job-detail"),
    path("jobs/<identifier>/cancel/", JobCancel.as_view(), name="job-cancel"),
    path("jobs/<identifier>/zombify/", JobZombify.as_view(), name="job-zombify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("orgs/", OrgList.as_view(), name="org-list"),
    path("orgs/new/", OrgCreate.as_view(), name="org-create"),
    path("orgs/<org_slug>/", OrgDetail.as_view(), name="org-detail"),
    path(
        "orgs/<org_slug>/new-project/",
        ProjectCreate.as_view(),
        name="project-create",
    ),
    path(
        "orgs/<org_slug>/<project_slug>/",
        ProjectDetail.as_view(),
        name="project-detail",
    ),
    path("settings/", Settings.as_view(), name="settings"),
    path("status/", Status.as_view(), name="status"),
    path("workspaces/", RedirectView.as_view(url="/")),
    path("workspaces/new/", WorkspaceCreate.as_view(), name="workspace-create"),
    path("__debug__/", include(debug_toolbar.urls)),
    path("<name>/", WorkspaceDetail.as_view(), name="workspace-detail"),
    path(
        "<name>/releases/<release>",
        WorkspaceReleaseView.as_view(),
        name="workspace-release",
    ),
    path(
        "<name>/archive-toggle/",
        WorkspaceArchiveToggle.as_view(),
        name="workspace-archive-toggle",
    ),
    path("<name>/logs/", WorkspaceLog.as_view(), name="workspace-logs"),
    path(
        "<name>/notifications-toggle/",
        WorkspaceNotificationsToggle.as_view(),
        name="workspace-notifications-toggle",
    ),
]
