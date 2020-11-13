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
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework import routers

from .api import JobAPIUpdate, JobRequestAPIList, JobViewSet, WorkspaceViewSet
from .views import (
    Index,
    JobDetail,
    JobRequestDetail,
    JobRequestList,
    JobRequestZombify,
    JobZombify,
    Status,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceLog,
)


router = routers.DefaultRouter()
router.register(r"jobs", JobViewSet, "jobs")
router.register(r"workspaces", WorkspaceViewSet, "workspaces")


api_patterns = [
    path("v1/", include(router.urls)),
    path("v2/job-requests/", JobRequestAPIList.as_view()),
    path("v2/jobs/", JobAPIUpdate.as_view()),
]

urlpatterns = [
    path("", Index.as_view()),
    path("", include("social_django.urls", namespace="social")),
    path("api/", include(api_patterns)),
    path("jobs/", JobRequestList.as_view(), name="job-list"),
    path("job-requests/<pk>/", JobRequestDetail.as_view(), name="job-request-detail"),
    path(
        "job-requests/<pk>/zombify/",
        JobRequestZombify.as_view(),
        name="job-request-zombify",
    ),
    path("jobs/<pk>/", JobDetail.as_view(), name="job-detail"),
    path("jobs/<pk>/zombify/", JobZombify.as_view(), name="job-zombify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("status/", Status.as_view(), name="status"),
    path("workspaces/", RedirectView.as_view(url="/")),
    path("workspaces/new/", WorkspaceCreate.as_view(), name="workspace-create"),
    path("__debug__/", include(debug_toolbar.urls)),
    path("<name>/", WorkspaceDetail.as_view(), name="workspace-detail"),
    path("<name>/logs/", WorkspaceLog.as_view(), name="workspace-logs"),
]
