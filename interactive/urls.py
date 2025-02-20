from django.urls import path

from jobserver.views.reports import PublishRequestCreate

from .views import AnalysisRequestCreate, AnalysisRequestDetail


app_name = "interactive"

urlpatterns = [
    path("", AnalysisRequestCreate.as_view(), name="analysis-create"),
    path("<str:slug>/", AnalysisRequestDetail.as_view(), name="analysis-detail"),
    path(
        "<str:slug>/publish/",
        PublishRequestCreate.as_view(),
        name="publish-request-create",
    ),
    path("<path>", AnalysisRequestCreate.as_view()),
]
