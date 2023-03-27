from django.contrib.auth.models import AnonymousUser

from jobserver.views.index import Index

from ....factories import (
    AnalysisRequestFactory,
    JobRequestFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_index_authenticated(rf, complete_application):
    user = UserFactory()

    complete_application.created_by = user
    complete_application.save()

    AnalysisRequestFactory(created_by=user)

    project1 = ProjectFactory()
    ProjectMembershipFactory(project=project1, user=user)
    workspace1 = WorkspaceFactory(project=project1)
    JobRequestFactory(workspace=workspace1, created_by=user)
    JobRequestFactory(workspace=workspace1, created_by=user)

    # another workspace in Project1 which the user did not create but should
    # still be able to see
    WorkspaceFactory(project=project1)

    project2 = ProjectFactory()
    ProjectMembershipFactory(project=project2, user=user)

    # create a lot of objects the user has access to so we can check our limits
    # are working as expected
    JobRequestFactory.create_batch(10, workspace=workspace1)
    ProjectMembershipFactory.create_batch(10, user=user)
    WorkspaceFactory.create_batch(10, project=project2)

    request = rf.get("/")
    request.user = user

    response = Index.as_view()(request)

    assert len(response.context_data["all_job_requests"]) == 10
    assert len(response.context_data["analysis_requests"]) == 1
    assert len(response.context_data["applications"]) == 1
    assert len(response.context_data["job_requests"]) == 2
    assert len(response.context_data["projects"]) == 5
    assert len(response.context_data["workspaces"]) == 5

    counts = response.context_data["counts"]
    assert counts["applications"] == 1
    assert counts["job_requests"] == 2
    assert counts["projects"] == 12
    assert counts["workspaces"] == 12


def test_index_unauthenticated(rf):
    JobRequestFactory.create_batch(10)

    request = rf.get("/")
    request.user = AnonymousUser()

    response = Index.as_view()(request)

    assert len(response.context_data["all_job_requests"]) == 10
