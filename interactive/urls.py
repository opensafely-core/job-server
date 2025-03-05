from django.urls import path

from jobserver.views.reports import PublishRequestCreate


app_name = "interactive"

urlpatterns = [
    path(
        "<str:slug>/publish/",
        PublishRequestCreate.as_view(),
        name="publish-request-create",
    ),
]
