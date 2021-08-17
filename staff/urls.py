from django.urls import include, path

from .views.backends import BackendDetail, BackendEdit, BackendList, BackendRotateToken
from .views.index import Index
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

user_urls = [
    path("", UserList.as_view(), name="user-list"),
    path("<username>/", UserDetail.as_view(), name="user-detail"),
]

urlpatterns = [
    path("", Index.as_view(), name="index"),
    path("backends/", include(backend_urls)),
    path("users/", include(user_urls)),
]
