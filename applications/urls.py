from django.urls import path
from django.views.generic import TemplateView

from .views import confirmation, page, sign_in, terms


app_name = "applications"

urlpatterns = [
    path(
        "apply/",
        TemplateView.as_view(template_name="applications/apply.html"),
        name="start",
    ),
    path("apply/sign-in", sign_in, name="sign-in"),
    path("apply/terms/", terms, name="terms"),
    path("applications/<int:pk>/page/<int:page_num>/", page, name="page"),
    path("applications/<int:pk>/confirmation/", confirmation, name="confirmation"),
]
