from django.urls import path

from .views import AnalysisRequestCreate, AnalysisRequestDetail


app_name = "interactive"

urlpatterns = [
    path("", AnalysisRequestCreate.as_view(), name="analysis-create"),
    path("<str:slug>/", AnalysisRequestDetail.as_view(), name="analysis-detail"),
]
