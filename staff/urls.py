from django.urls import include, path

from .views import sentry
from .views.analysis_requests import (
    AnalysisRequestDetail,
    AnalysisRequestList,
    AnalysisRequestResubmit,
)
from .views.applications import (
    ApplicationApprove,
    ApplicationDetail,
    ApplicationEdit,
    ApplicationList,
    ApplicationRemove,
    ApplicationRestore,
)
from .views.backends import (
    BackendCreate,
    BackendDetail,
    BackendEdit,
    BackendList,
    BackendRotateToken,
)
from .views.dashboards.copiloting import Copiloting
from .views.dashboards.index import DashboardIndex
from .views.dashboards.projects import ProjectsDashboard
from .views.dashboards.repos import PrivateReposDashboard, ReposWithMultipleProjects
from .views.index import Index
from .views.job_requests import JobRequestDetail, JobRequestList
from .views.orgs import (
    OrgCreate,
    OrgDetail,
    OrgEdit,
    OrgList,
    OrgRemoveGitHubOrg,
    OrgRemoveMember,
    org_add_github_org,
)
from .views.projects import (
    ProjectAddMember,
    ProjectCreate,
    ProjectDetail,
    ProjectEdit,
    ProjectLinkApplication,
    ProjectList,
    ProjectMembershipEdit,
    ProjectMembershipRemove,
)
from .views.redirects import RedirectDelete, RedirectDetail, RedirectList
from .views.reports import (
    ReportDetail,
    ReportList,
    ReportPublishRequestApprove,
    ReportPublishRequestReject,
)
from .views.repos import RepoDetail, RepoList, RepoSignOff
from .views.researchers import ResearcherEdit
from .views.users import (
    UserClearRoles,
    UserCreate,
    UserDetail,
    UserList,
    UserRoleList,
    UserSetOrgs,
)
from .views.workspaces import WorkspaceDetail, WorkspaceEdit, WorkspaceList


app_name = "staff"


analysis_request_urls = [
    path("", AnalysisRequestList.as_view(), name="analysis-request-list"),
    path(
        "<str:slug>/", AnalysisRequestDetail.as_view(), name="analysis-request-detail"
    ),
    path(
        "<str:slug>/resubmit",
        AnalysisRequestResubmit.as_view(),
        name="analysis-request-resubmit",
    ),
]

application_urls = [
    path("", ApplicationList.as_view(), name="application-list"),
    path("<str:pk_hash>/", ApplicationDetail.as_view(), name="application-detail"),
    path(
        "<str:pk_hash>/approve/",
        ApplicationApprove.as_view(),
        name="application-approve",
    ),
    path("<str:pk_hash>/edit/", ApplicationEdit.as_view(), name="application-edit"),
    path(
        "<str:pk_hash>/delete/", ApplicationRemove.as_view(), name="application-delete"
    ),
    path(
        "<str:pk_hash>/restore/",
        ApplicationRestore.as_view(),
        name="application-restore",
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

dashboard_urls = [
    path("", DashboardIndex.as_view(), name="index"),
    path("copiloting/", Copiloting.as_view(), name="copiloting"),
    path("project/", ProjectsDashboard.as_view(), name="projects"),
    path("repos/", PrivateReposDashboard.as_view(), name="repos"),
    path(
        "repos-with-multiple-projects/",
        ReposWithMultipleProjects.as_view(),
        name="repos-with-multiple-projects",
    ),
]

job_request_urls = [
    path("", JobRequestList.as_view(), name="job-request-list"),
    path("<int:pk>/", JobRequestDetail.as_view(), name="job-request-detail"),
]

org_urls = [
    path("", OrgList.as_view(), name="org-list"),
    path("add/", OrgCreate.as_view(), name="org-create"),
    path("<slug>/", OrgDetail.as_view(), name="org-detail"),
    path("<slug>/add-github-org/", org_add_github_org, name="org-add-github-org"),
    path("<slug>/edit/", OrgEdit.as_view(), name="org-edit"),
    path(
        "<slug>/remove-member/", OrgRemoveMember.as_view(), name="org-membership-remove"
    ),
    path(
        "<slug>/remove-github-org/",
        OrgRemoveGitHubOrg.as_view(),
        name="org-remove-github-org",
    ),
]
project_urls = [
    path("", ProjectList.as_view(), name="project-list"),
    path("add/", ProjectCreate.as_view(), name="project-create"),
    path("<slug>/", ProjectDetail.as_view(), name="project-detail"),
    path("<slug>/add-member/", ProjectAddMember.as_view(), name="project-add-member"),
    path("<slug>/edit/", ProjectEdit.as_view(), name="project-edit"),
    path(
        "<slug>/link-application/",
        ProjectLinkApplication.as_view(),
        name="project-link-application",
    ),
    path(
        "<slug>/members/<pk>/edit/",
        ProjectMembershipEdit.as_view(),
        name="project-membership-edit",
    ),
    path(
        "<slug>/members/<pk>/remove/",
        ProjectMembershipRemove.as_view(),
        name="project-membership-remove",
    ),
]

redirect_urls = [
    path("", RedirectList.as_view(), name="redirect-list"),
    path("<int:pk>/", RedirectDetail.as_view(), name="redirect-detail"),
    path("<int:pk>/delete/", RedirectDelete.as_view(), name="redirect-delete"),
]

repo_urls = [
    path("", RepoList.as_view(), name="repo-list"),
    path("<repo_url>/", RepoDetail.as_view(), name="repo-detail"),
    path("<repo_url>/sign-off/", RepoSignOff.as_view(), name="repo-sign-off"),
]

report_urls = [
    path("", ReportList.as_view(), name="report-list"),
    path("<int:pk>/", ReportDetail.as_view(), name="report-detail"),
    path(
        "<int:pk>/publish-requests/<int:publish_request_pk>/",
        include(
            [
                path(
                    "approve/",
                    ReportPublishRequestApprove.as_view(),
                    name="publish-request-approve",
                ),
                path(
                    "reject/",
                    ReportPublishRequestReject.as_view(),
                    name="publish-request-reject",
                ),
            ]
        ),
    ),
]

researcher_urls = [
    path("<int:pk>/edit/", ResearcherEdit.as_view(), name="researcher-edit"),
]


sentry_urls = [
    path("", sentry.index, name="index"),
    path("error", sentry.error, name="error"),
    path("message", sentry.message, name="message"),
]


user_urls = [
    path("", UserList.as_view(), name="user-list"),
    path("add/", UserCreate.as_view(), name="user-create"),
    path("<username>/", UserDetail.as_view(), name="user-detail"),
    path("<username>/roles/", UserRoleList.as_view(), name="user-role-list"),
    path("<username>/roles/clear/", UserClearRoles.as_view(), name="user-clear-roles"),
    path("<username>/set-orgs/", UserSetOrgs.as_view(), name="user-set-orgs"),
]

workspace_urls = [
    path("", WorkspaceList.as_view(), name="workspace-list"),
    path("<slug>/", WorkspaceDetail.as_view(), name="workspace-detail"),
    path("<slug>/edit/", WorkspaceEdit.as_view(), name="workspace-edit"),
]

urlpatterns = [
    path("", Index.as_view(), name="index"),
    path("analysis-requests/", include(analysis_request_urls)),
    path("applications/", include(application_urls)),
    path("backends/", include(backend_urls)),
    path("dashboards/", include((dashboard_urls, "dashboards"), namespace="dashboard")),
    path("job-requests/", include(job_request_urls)),
    path("orgs/", include(org_urls)),
    path("projects/", include(project_urls)),
    path("redirects/", include(redirect_urls)),
    path("repos/", include(repo_urls)),
    path("reports/", include(report_urls)),
    path("researchers/", include(researcher_urls)),
    path("sentry/", include((sentry_urls, "sentry"), namespace="sentry")),
    path("users/", include(user_urls)),
    path("workspaces/", include(workspace_urls)),
]
