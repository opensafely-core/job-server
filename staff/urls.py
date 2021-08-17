from django.urls import include, path

from .views.backends import BackendDetail, BackendEdit, BackendList, BackendRotateToken
from .views.index import Index
from .views.projects import ProjectDetail, ProjectEdit, ProjectList
from .views.users import UserDetail, UserList


app_name = "staff"

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

project_urls = [
    path("", ProjectList.as_view(), name="project-list"),
    path("<slug>/", ProjectDetail.as_view(), name="project-detail"),
    path("<slug>/edit/", ProjectEdit.as_view(), name="project-edit"),
]

user_urls = [
    path("", UserList.as_view(), name="user-list"),
    path("<username>/", UserDetail.as_view(), name="user-detail"),
]

urlpatterns = [
    path("", Index.as_view(), name="index"),
    path("backends/", include(backend_urls)),
    path("projects/", include(project_urls)),
    path("users/", include(user_urls)),
]
