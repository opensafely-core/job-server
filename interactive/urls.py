from django.urls import path

from jobserver.views.reports import PublishRequestCreate

from .views import AnalysisRequestDetail


app_name = "interactive"

urlpatterns = [
    path("<str:slug>/", AnalysisRequestDetail.as_view(), name="analysis-detail"),
    path(
        "<str:slug>/publish/",
        PublishRequestCreate.as_view(),
        name="publish-request-create",
    ),
]
