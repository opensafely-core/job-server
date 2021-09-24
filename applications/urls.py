from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

from .views import (
    ResearcherCreate,
    ResearcherDelete,
    ResearcherEdit,
    confirmation,
    page,
    sign_in,
    terms,
)


app_name = "applications"

researcher_urls = [
    path("", RedirectView.as_view(pattern_name="applications:researcher-add")),
    path("add", ResearcherCreate.as_view(), name="researcher-add"),
    path(
        "<int:researcher_pk>/delete/",
        ResearcherDelete.as_view(),
        name="researcher-delete",
    ),
    path("<int:researcher_pk>/edit/", ResearcherEdit.as_view(), name="researcher-edit"),
]
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
    path("applications/<int:pk>/researchers/", include(researcher_urls)),
]
