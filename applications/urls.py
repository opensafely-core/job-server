from django.urls import path

from .views import ApplicationDetail, ApplicationProcess, Apply, application


app_name = "applications"

urlpatterns = [
    path("", application, name="application"),
    path("applications/<int:pk>/", ApplicationDetail.as_view()),
    path(
        "applications/<int:pk>/page/<int:page_num>/",
        ApplicationProcess.as_view(),
        name="application-process",
    ),
    path("apply/", Apply.as_view(), name="apply"),
]
