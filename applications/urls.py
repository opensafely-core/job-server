from django.urls import path

from .views import confirmation, new, page


app_name = "applications"

urlpatterns = [
    path(
        "applications/new/",
        new,
        name="new",
    ),
    path(
        "applications/<int:pk>/page/<int:page_num>/",
        page,
        name="page",
    ),
    path(
        "applications/<int:pk>/confirmation/",
        confirmation,
        name="confirmation",
    ),
]
