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
from rest_framework import routers

from .api_views import JobViewSet, WorkspaceViewSet
from .views import (
    JobCreate,
    JobDetail,
    JobList,
    Login,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceList,
)


router = routers.DefaultRouter()
router.register(r"jobs", JobViewSet, "jobs")
router.register(r"workspaces", WorkspaceViewSet, "workspaces")


urlpatterns = [
    path("", RedirectView.as_view(pattern_name="job-list")),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    path("jobs/", JobList.as_view(), name="job-list"),
    path("jobs/new/", JobCreate.as_view(), name="job-create"),
    path("jobs/<pk>/", JobDetail.as_view(), name="job-detail"),
    path("login/", Login.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("workspaces/", WorkspaceList.as_view(), name="workspace-list"),
    path("workspaces/new/", WorkspaceCreate.as_view(), name="workspace-create"),
    path("workspaces/<pk>/", WorkspaceDetail.as_view(), name="workspace-detail"),
    path("__debug__/", include(debug_toolbar.urls)),
]
