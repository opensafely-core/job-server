from django.urls import include, path

from .views.applications import (
    ApplicationApprove,
    ApplicationDetail,
    ApplicationEdit,
    ApplicationList,
)
from .views.backends import (
    BackendCreate,
    BackendDetail,
    BackendEdit,
    BackendList,
    BackendRotateToken,
)
from .views.index import Index
from .views.orgs import (
    OrgCreate,
    OrgDetail,
    OrgEdit,
    OrgList,
    OrgProjectCreate,
    OrgRemoveMember,
)
from .views.projects import (
    ProjectAddMember,
    ProjectDetail,
    ProjectEdit,
    ProjectList,
    ProjectRemoveMember,
)
from .views.repos import RepoList
from .views.users import UserDetail, UserList, UserSetOrgs
from .views.workspaces import WorkspaceDetail, WorkspaceList


app_name = "staff"

application_urls = [
    path("", ApplicationList.as_view(), name="application-list"),
    path("<str:pk_hash>/", ApplicationDetail.as_view(), name="application-detail"),
    path("<str:pk_hash>/edit/", ApplicationEdit.as_view(), name="application-edit"),
    path(
        "<str:pk_hash>/approve/",
        ApplicationApprove.as_view(),
        name="application-approve",
    ),
]

backend_urls = [
    path("", BackendList.as_view(), name="backend-list"),
    path("add/", BackendCreate.as_view(), name="backend-create"),
    path("<int:pk>/", BackendDetail.as_view(), name="backend-detail"),
    path("<int:pk>/edit/", BackendEdit.as_view(), name="backend-edit"),
    path(
        "<int:pk>/rotate-token/",
        BackendRotateToken.as_view(),
        name="backend-rotate-token",
    ),
]

org_urls = [
    path("", OrgList.as_view(), name="org-list"),
    path("add/", OrgCreate.as_view(), name="org-create"),
    path("<slug>/", OrgDetail.as_view(), name="org-detail"),
    path("<slug>/add-project/", OrgProjectCreate.as_view(), name="org-project-create"),
    path("<slug>/edit/", OrgEdit.as_view(), name="org-edit"),
    path("<slug>/remove-member/", OrgRemoveMember.as_view(), name="org-remove-member"),
]
project_urls = [
    path("", ProjectList.as_view(), name="project-list"),
    path("<slug>/", ProjectDetail.as_view(), name="project-detail"),
    path("<slug>/add-member/", ProjectAddMember.as_view(), name="project-add-member"),
    path("<slug>/edit/", ProjectEdit.as_view(), name="project-edit"),
    path(
        "<slug>/remove-member/",
        ProjectRemoveMember.as_view(),
        name="project-remove-member",
    ),
]

user_urls = [
    path("", UserList.as_view(), name="user-list"),
    path("<username>/", UserDetail.as_view(), name="user-detail"),
    path("<username>/set-orgs/", UserSetOrgs.as_view(), name="user-set-orgs"),
]

workspace_urls = [
    path("", WorkspaceList.as_view(), name="workspace-list"),
    path("<slug>/", WorkspaceDetail.as_view(), name="workspace-detail"),
]

urlpatterns = [
    path("", Index.as_view(), name="index"),
    path("applications/", include(application_urls)),
    path("backends/", include(backend_urls)),
    path("orgs/", include(org_urls)),
    path("projects/", include(project_urls)),
    path("repos/", RepoList.as_view(), name="repo-list"),
    path("users/", include(user_urls)),
    path("workspaces/", include(workspace_urls)),
]
