from django.urls import include, path
from django.views.generic import RedirectView

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
    # The JobServer applications process is closed for new business, the
    # ProjectCreate form in the staff area will allow creating new projects.
    # Permanently redirect all /apply paths and subpaths to the new site. We
    # may remove more of the applications app later but it remains visible.
    path(
        "apply/",
        RedirectView.as_view(
            url="https://www.opensafely.org/opensafely-is-open-for-submissions/",
            permanent=True,
        ),
    ),
    path(
        "apply/<path:subpath>",
        RedirectView.as_view(
            url="https://www.opensafely.org/opensafely-is-open-for-submissions/",
            permanent=True,
        ),
    ),
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
