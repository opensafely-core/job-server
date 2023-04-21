from django.urls import path

from jobserver.views.reports import (
    ReportPublishRequestCreate,
    ReportPublishRequestUpdate,
)

from .views import AnalysisReportUpdate, AnalysisRequestCreate, AnalysisRequestDetail


app_name = "interactive"

urlpatterns = [
    path("", AnalysisRequestCreate.as_view(), name="analysis-create"),
    path("<slug:slug>/", AnalysisRequestDetail.as_view(), name="analysis-detail"),
    path("<str:slug>/", AnalysisRequestDetail.as_view(), name="analysis-detail"),
    path("<str:slug>/update", AnalysisReportUpdate.as_view(), name="report-update"),
    path(
        "<str:slug>/publish/",
        ReportPublishRequestCreate.as_view(),
        name="report-publish-request-create",
    ),
    path(
        "<str:slug>/publish/<pk>/",
        ReportPublishRequestUpdate.as_view(),
        name="report-publish-request-update",
    ),
    path("<path>", AnalysisRequestCreate.as_view()),
]
