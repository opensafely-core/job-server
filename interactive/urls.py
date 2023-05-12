from django.urls import path

from jobserver.views.reports import ReportPublishRequestCreate

from .views import AnalysisRequestCreate, AnalysisRequestDetail, ReportEdit


app_name = "interactive"

urlpatterns = [
    path("", AnalysisRequestCreate.as_view(), name="analysis-create"),
    path("<slug:slug>/", AnalysisRequestDetail.as_view(), name="analysis-detail"),
    path("<str:slug>/", AnalysisRequestDetail.as_view(), name="analysis-detail"),
    path("<str:slug>/edit/", ReportEdit.as_view(), name="report-edit"),
    path(
        "<str:slug>/publish/",
        ReportPublishRequestCreate.as_view(),
        name="report-publish-request-create",
    ),
    path("<path>", AnalysisRequestCreate.as_view()),
]
