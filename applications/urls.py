from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

from .views import (
    ApplicationList,
    ApplicationRemove,
    ApplicationRestore,
    Confirmation,
    PageRedirect,
    ResearcherCreate,
    ResearcherDelete,
    ResearcherEdit,
    page,
    sign_in,
    terms,
)


app_name = "applications"

researcher_urls = [
    path("", RedirectView.as_view(pattern_name="applications:researcher-add")),
    path("add/", ResearcherCreate.as_view(), name="researcher-add"),
    path(
        "<int:researcher_pk>/",
        RedirectView.as_view(
            pattern_name="applications:researcher-edit", query_string=True
        ),
        name="researcher-detail",
    ),
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
    path("applications/", ApplicationList.as_view(), name="list"),
    path("applications/<str:pk_hash>/", PageRedirect.as_view(), name="detail"),
    path("applications/<str:pk_hash>/page/<str:key>/", page, name="page"),
    path(
        "applications/<str:pk_hash>/confirmation/",
        Confirmation.as_view(),
        name="confirmation",
    ),
    path(
        "applications/<str:pk_hash>/delete/", ApplicationRemove.as_view(), name="delete"
    ),
    path(
        "applications/<str:pk_hash>/restore/",
        ApplicationRestore.as_view(),
        name="restore",
    ),
    path("applications/<str:pk_hash>/researchers/", include(researcher_urls)),
]
