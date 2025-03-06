from django.urls import path

from .views import AnalysisRequestDetail


app_name = "interactive"

urlpatterns = [
    path("<str:slug>/", AnalysisRequestDetail.as_view(), name="analysis-detail"),
]
