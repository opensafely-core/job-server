from datetime import timedelta

import pytest
from django.core import signing
from django.urls import reverse
from django.utils import timezone

from jobserver.authorization.roles import (
    CoreDeveloper,
    DataInvestigator,
    OrgCoordinator,
    OutputChecker,
    OutputPublisher,
    ProjectCollaborator,
    ProjectDeveloper,
)
from jobserver.models import (
    Backend,
    JobRequest,
    ProjectInvitation,
    ProjectMembership,
    User,
)

from ...factories import (
    JobFactory,
    JobRequestFactory,
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    ProjectInvitationFactory,
    ProjectMembershipFactory,
    UserFactory,
    WorkspaceFactory,
)
from ...utils import minutes_ago, seconds_ago


@pytest.mark.django_db
def test_job_get_absolute_url():
    job = JobFactory()

    url = job.get_absolute_url()

    assert url == reverse(
        "job-detail",
        kwargs={
            "org_slug": job.job_request.workspace.project.org.slug,
            "project_slug": job.job_request.workspace.project.slug,
            "workspace_slug": job.job_request.workspace.name,
            "pk": job.job_request.pk,
            "identifier": job.identifier,
        },
    )


@pytest.mark.django_db
def test_job_get_cancel_url():
    job = JobFactory()

    url = job.get_cancel_url()

    assert url == reverse(
        "job-cancel",
        kwargs={
            "org_slug": job.job_request.workspace.project.org.slug,
            "project_slug": job.job_request.workspace.project.slug,
            "workspace_slug": job.job_request.workspace.name,
            "pk": job.job_request.pk,
            "identifier": job.identifier,
        },
    )


@pytest.mark.django_db
def test_job_is_missing_updates_above_threshold():
    last_update = minutes_ago(timezone.now(), 50)
    job = JobFactory(completed_at=None, updated_at=last_update)

    assert job.is_missing_updates


@pytest.mark.django_db
def test_job_is_missing_updates_below_threshold():
    last_update = minutes_ago(timezone.now(), 29)
    job = JobFactory(completed_at=None, updated_at=last_update)

    assert not job.is_missing_updates


@pytest.mark.django_db
def test_job_is_missing_updates_missing_updated_at():
    assert not JobFactory(status="pending", updated_at=None).is_missing_updates


@pytest.mark.django_db
def test_job_is_missing_updates_completed():
    assert not JobFactory(status="failed").is_missing_updates


@pytest.mark.django_db
def test_job_runtime():
    duration = timedelta(hours=1, minutes=2, seconds=3)
    started_at = timezone.now() - duration
    job = JobFactory(
        status="succeeded", started_at=started_at, completed_at=timezone.now()
    )

    assert job.runtime.hours == 1
    assert job.runtime.minutes == 2
    assert job.runtime.seconds == 3


@pytest.mark.django_db
def test_job_runtime_not_completed():
    job = JobFactory(status="running", started_at=timezone.now())

    # an uncompleted job has no runtime
    assert job.runtime is None


@pytest.mark.django_db
def test_job_runtime_not_started():
    job = JobFactory(status="pending")

    # an unstarted job has no runtime
    assert job.runtime is None


@pytest.mark.django_db
def test_job_runtime_without_timestamps():
    job = JobFactory(status="succeeded", started_at=None, completed_at=None)

    assert job.runtime is None


@pytest.mark.django_db
def test_job_str():
    job = JobFactory(action="Run")

    assert str(job) == f"Run ({job.pk})"


@pytest.mark.django_db
def test_jobrequest_completed_at_no_jobs():
    assert not JobRequestFactory().completed_at


@pytest.mark.django_db
def test_jobrequest_completed_at_success():
    job_request = JobRequestFactory()

    job1, job2 = JobFactory.create_batch(2, job_request=job_request, status="succeeded")

    jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
    assert jr.completed_at == job2.completed_at


@pytest.mark.django_db
def test_jobrequest_completed_at_while_incomplete():
    job_request = JobRequestFactory()

    JobFactory(job_request=job_request, completed_at=timezone.now())
    JobFactory(job_request=job_request)

    jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
    assert not jr.completed_at


@pytest.mark.django_db
def test_jobrequest_get_absolute_url():
    job_request = JobRequestFactory()

    url = job_request.get_absolute_url()

    assert url == reverse(
        "job-request-detail",
        kwargs={
            "org_slug": job_request.workspace.project.org.slug,
            "project_slug": job_request.workspace.project.slug,
            "workspace_slug": job_request.workspace.name,
            "pk": job_request.pk,
        },
    )


@pytest.mark.django_db
def test_jobrequest_get_cancel_url():
    job_request = JobRequestFactory()

    url = job_request.get_cancel_url()

    assert url == reverse(
        "job-request-cancel",
        kwargs={
            "org_slug": job_request.workspace.project.org.slug,
            "project_slug": job_request.workspace.project.slug,
            "workspace_slug": job_request.workspace.name,
            "pk": job_request.pk,
        },
    )


@pytest.mark.django_db
def test_jobrequest_get_project_yaml_url_no_sha():
    workspace = WorkspaceFactory(repo="http://example.com/opensafely/some_repo")
    job_request = JobRequestFactory(workspace=workspace)

    url = job_request.get_file_url("test-blah.foo")

    assert url == "http://example.com/opensafely/some_repo"


@pytest.mark.django_db
def test_jobrequest_get_project_yaml_url_success():
    workspace = WorkspaceFactory(repo="http://example.com/opensafely/some_repo")
    job_request = JobRequestFactory(workspace=workspace, sha="abc123")

    url = job_request.get_file_url("test-blah.foo")

    assert url == "http://example.com/opensafely/some_repo/blob/abc123/test-blah.foo"


@pytest.mark.django_db
def test_jobrequest_get_repo_url_no_sha():
    workspace = WorkspaceFactory(repo="http://example.com/opensafely/some_repo")
    job_request = JobRequestFactory(workspace=workspace)

    url = job_request.get_repo_url()

    assert url == "http://example.com/opensafely/some_repo"


@pytest.mark.django_db
def test_jobrequest_get_repo_url_success():
    workspace = WorkspaceFactory(repo="http://example.com/opensafely/some_repo")
    job_request = JobRequestFactory(workspace=workspace, sha="abc123")

    url = job_request.get_repo_url()

    assert url == "http://example.com/opensafely/some_repo/tree/abc123"


@pytest.mark.django_db
def test_jobrequest_is_completed():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
    assert jr.is_completed


@pytest.mark.django_db
def test_jobrequest_is_invalid():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, action="__error__")

    assert job_request.is_invalid


@pytest.mark.django_db
def test_jobrequest_num_completed_no_jobs():
    assert JobRequestFactory().num_completed == 0


@pytest.mark.django_db
def test_job_request_num_completed_success():
    job_request = JobRequestFactory()

    job1, job2 = JobFactory.create_batch(2, job_request=job_request, status="succeeded")

    assert job_request.num_completed == 2


@pytest.mark.django_db
def test_jobrequest_runtime_one_job_missing_completed_at(freezer):
    job_request = JobRequestFactory()

    now = timezone.now()

    JobFactory(
        job_request=job_request,
        status="succeeded",
        started_at=minutes_ago(now, 3),
        completed_at=minutes_ago(now, 2),
    )
    JobFactory(
        job_request=job_request,
        status="running",
        started_at=minutes_ago(now, 1),
        completed_at=None,
    )

    jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
    assert jr.started_at
    assert not jr.completed_at

    # combined _completed_ Job runtime is 0 because the failed job has no
    # runtime (it never started)
    assert jr.runtime
    assert jr.runtime.hours == 0
    assert jr.runtime.minutes == 1
    assert jr.runtime.seconds == 0


@pytest.mark.django_db
def test_jobrequest_runtime_one_job_missing_started_at(freezer):
    job_request = JobRequestFactory()

    now = timezone.now()

    JobFactory(
        job_request=job_request,
        status="failed",
        started_at=minutes_ago(now, 5),
        completed_at=minutes_ago(now, 3),
    )
    JobFactory(
        job_request=job_request,
        status="failed",
        started_at=None,
        completed_at=timezone.now(),
    )

    jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
    assert jr.started_at
    assert jr.completed_at

    # combined _completed_ Job runtime is 2 minutes because the second job
    # failed before it started
    assert jr.runtime
    assert jr.runtime.hours == 0
    assert jr.runtime.minutes == 2
    assert jr.runtime.seconds == 0


@pytest.mark.django_db
def test_jobrequest_runtime_no_jobs():
    assert not JobRequestFactory().runtime


@pytest.mark.django_db
def test_jobrequest_runtime_not_completed(freezer):
    job_request = JobRequestFactory()

    now = timezone.now()

    JobFactory(
        job_request=job_request,
        status="succeeded",
        started_at=minutes_ago(now, 2),
        completed_at=minutes_ago(now, 1),
    )
    JobFactory(
        job_request=job_request,
        status="running",
        started_at=seconds_ago(now, 30),
    )

    jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
    assert jr.started_at
    assert not jr.completed_at

    # combined _completed_ Job runtime is 1 minute
    assert jr.runtime
    assert jr.runtime.hours == 0
    assert jr.runtime.minutes == 1
    assert jr.runtime.seconds == 0


@pytest.mark.django_db
def test_jobrequest_runtime_not_started():
    job_request = JobRequestFactory()

    JobFactory(job_request=job_request, status="running")
    JobFactory(job_request=job_request, status="pending")

    assert not job_request.runtime


@pytest.mark.django_db
def test_jobrequest_runtime_success():
    job_request = JobRequestFactory()

    start = timezone.now() - timedelta(hours=1)

    JobFactory(
        job_request=job_request,
        status="succeeded",
        started_at=start,
        completed_at=start + timedelta(minutes=1),
    )
    JobFactory(
        job_request=job_request,
        status="failed",
        started_at=start + timedelta(minutes=2),
        completed_at=start + timedelta(minutes=3),
    )

    assert job_request.runtime
    assert job_request.runtime.hours == 0
    assert job_request.runtime.minutes == 2
    assert job_request.runtime.seconds == 0


@pytest.mark.django_db
def test_jobrequest_started_at_no_jobs():
    assert not JobRequestFactory().started_at


@pytest.mark.django_db
def test_jobrequest_started_at_success():
    job_request = JobRequestFactory()

    JobFactory(job_request=job_request, started_at=timezone.now())
    JobFactory(job_request=job_request, started_at=timezone.now())

    assert job_request.started_at


@pytest.mark.django_db
def test_jobrequest_status_all_jobs_the_same(subtests):
    status_groups = [
        ["failed", "failed", "failed", "failed"],
        ["pending", "pending", "pending", "pending"],
        ["running", "running", "running", "running"],
        ["succeeded", "succeeded", "succeeded", "succeeded"],
    ]
    for statuses in status_groups:
        with subtests.test(statuses=statuses):
            job_request = JobRequestFactory()
            for status in statuses:
                JobFactory(job_request=job_request, status=status)

            jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
            assert jr.status == statuses[0]


@pytest.mark.django_db
def test_jobrequest_status_running_in_job_statuses():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="running")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
    assert jr.status == "running"


@pytest.mark.django_db
def test_jobrequest_status_running_not_in_job_statues():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
    assert jr.status == "running"


@pytest.mark.django_db
def test_jobrequest_status_failed():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
    assert jr.status == "failed"


@pytest.mark.django_db
def test_jobrequest_status_unknown():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="foo")
    JobFactory(job_request=job_request, status="bar")

    jr = JobRequest.objects.prefetch_related("jobs").get(pk=job_request.pk)
    assert jr.status == "unknown"


@pytest.mark.django_db
def test_jobrequest_status_uses_prefetch_cache(django_assert_num_queries):
    for i in range(5):
        jr = JobRequestFactory()
        JobFactory.create_batch(5, job_request=jr)

    with django_assert_num_queries(2):
        # 1. select JobRequests
        # 2. select Jobs for those JobRequests
        [jr.status for jr in JobRequest.objects.prefetch_related("jobs")]


@pytest.mark.django_db
def test_jobrequest_status_without_prefetching_jobs(django_assert_num_queries):
    job_request = JobRequestFactory()
    JobFactory.create_batch(5, job_request=job_request)

    with pytest.raises(Exception, match="JobRequest queries must prefetch jobs."):
        job_request.status


@pytest.mark.django_db
def test_org_get_absolute_url():
    org = OrgFactory()
    url = org.get_absolute_url()
    assert url == reverse("org-detail", kwargs={"org_slug": org.slug})


@pytest.mark.django_db
def test_org_populates_slug():
    assert OrgFactory(name="Test Org", slug="").slug == "test-org"


@pytest.mark.django_db
def test_org_str():
    assert str(OrgFactory(name="Test Org")) == "Test Org"


@pytest.mark.django_db
def test_orgmembership_str():
    org = OrgFactory(name="EBMDataLab")
    user = UserFactory(username="ben")

    membership = OrgMembershipFactory(org=org, user=user)

    assert str(membership) == "ben | EBMDataLab"


@pytest.mark.django_db
def test_project_get_absolute_url():
    org = OrgFactory(name="test-org")
    project = ProjectFactory(org=org)
    url = project.get_absolute_url()
    assert url == reverse(
        "project-detail", kwargs={"org_slug": org.slug, "project_slug": project.slug}
    )


@pytest.mark.django_db
def test_projectmembership_get_edit_url():
    org = OrgFactory(name="test-org")
    project = ProjectFactory(org=org)
    user = UserFactory()

    membership = ProjectMembershipFactory(project=project, user=user)

    url = membership.get_edit_url()
    assert url == reverse(
        "project-membership-edit",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "pk": membership.pk,
        },
    )


@pytest.mark.django_db
def test_projectmembership_get_remove_url():
    org = OrgFactory(name="test-org")
    project = ProjectFactory(org=org)
    user = UserFactory()

    membership = ProjectMembershipFactory(project=project, user=user)

    url = membership.get_remove_url()
    assert url == reverse(
        "project-membership-remove",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "pk": membership.pk,
        },
    )


@pytest.mark.django_db
def test_project_get_invitation_url():
    org = OrgFactory(name="test-org")
    project = ProjectFactory(org=org)
    url = project.get_invitation_url()
    assert url == reverse(
        "project-invitation-create",
        kwargs={"org_slug": org.slug, "project_slug": project.slug},
    )


@pytest.mark.django_db
def test_project_get_releases_url():
    project = ProjectFactory()

    url = project.get_releases_url()

    assert url == reverse(
        "project-release-list",
        kwargs={
            "org_slug": project.org.slug,
            "project_slug": project.slug,
        },
    )


@pytest.mark.django_db
def test_project_get_settings_url():
    org = OrgFactory(name="test-org")
    project = ProjectFactory(org=org)
    url = project.get_settings_url()
    assert url == reverse(
        "project-settings", kwargs={"org_slug": org.slug, "project_slug": project.slug}
    )


@pytest.mark.django_db
def test_project_populates_slug():
    assert ProjectFactory(name="Test Project", slug="").slug == "test-project"


@pytest.mark.django_db
def test_project_str():
    project = ProjectFactory(
        org=OrgFactory(name="test-org"),
        name="Very Good Project",
    )
    assert str(project) == "test-org | Very Good Project"


@pytest.mark.django_db
def test_projectinvitation_create_membership():
    invite = ProjectInvitationFactory(accepted_at=None, membership=None)

    assert not ProjectMembership.objects.exists()

    invite.create_membership()

    assert ProjectMembership.objects.exists()

    membership = ProjectMembership.objects.first()
    assert membership.project == invite.project
    assert membership.user == invite.user

    assert invite.accepted_at is not None
    assert invite.membership == membership


@pytest.mark.django_db
def test_projectinvitation_get_cancel_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    invite = ProjectInvitationFactory(project=project)
    url = invite.get_cancel_url()

    assert url == reverse(
        "project-cancel-invite",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
        },
    )


@pytest.mark.django_db
def test_projectinvitation_get_from_signed_pk_success():
    invite_a = ProjectInvitationFactory()

    invite_b = ProjectInvitation.get_from_signed_pk(invite_a.signed_pk)

    assert invite_b == invite_a


def test_projectinvitation_get_from_signed_pk_with_bad_value():
    with pytest.raises(signing.BadSignature):
        ProjectInvitation.get_from_signed_pk("test")


@pytest.mark.django_db
def test_projectinvitation_get_from_signed_pk_with_unknown_pk():
    signed_pk = ProjectInvitation.signer().sign(0)

    with pytest.raises(ProjectInvitation.DoesNotExist):
        ProjectInvitation.get_from_signed_pk(signed_pk)


@pytest.mark.django_db
def test_projectinvitation_get_invitation_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    invite = ProjectInvitationFactory(project=project)
    url = invite.get_invitation_url()

    assert url == reverse(
        "project-accept-invite",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "signed_pk": invite.signed_pk,
        },
    )


@pytest.mark.django_db
def test_projectinvitation_signed_pk():
    invite = ProjectInvitationFactory()

    assert ProjectInvitation.signer().sign(invite.pk) == invite.signed_pk


def test_projectinvitation_signer():
    signer = ProjectInvitation.signer()

    # check the salt for this model is set up correctly
    assert signer.salt == "project-invitation"


@pytest.mark.django_db
def test_projectinvitation_str():
    project = ProjectFactory(name="DataLab")
    user = UserFactory(username="ben")

    invitation = ProjectInvitationFactory(project=project, user=user)

    assert str(invitation) == "ben | DataLab"


@pytest.mark.django_db
def test_projectmembership_str():
    project = ProjectFactory(name="DataLab")
    user = UserFactory(username="ben")

    membership = ProjectMembershipFactory(project=project, user=user)

    assert str(membership) == "ben | DataLab"


@pytest.mark.django_db
def test_user_name_with_first_and_last_name():
    user = UserFactory(first_name="first", last_name="last")

    assert user.name == "first last"


@pytest.mark.django_db
def test_user_name_without_first_and_last_name():
    user = UserFactory()
    assert user.name == user.username


@pytest.mark.django_db
def test_user_get_absolute_url():
    user = UserFactory()

    url = user.get_absolute_url()

    assert url == reverse(
        "user-detail",
        kwargs={
            "username": user.username,
        },
    )


@pytest.mark.django_db
def test_user_get_all_permissions():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    user = UserFactory(roles=[CoreDeveloper])

    OrgMembershipFactory(org=org, user=user, roles=[OrgCoordinator])
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    output = user.get_all_permissions()
    expected = {
        "global": [
            "job_cancel",
            "manage_backends",
            "manage_project_members",
            "manage_project_workspaces",
            "manage_users",
            "org_create",
            "project_invite_members",
            "run_job",
        ],
        "orgs": [{"slug": org.slug, "permissions": []}],
        "projects": [
            {
                "slug": project.slug,
                "permissions": [
                    "job_cancel",
                    "manage_project_workspaces",
                    "run_job",
                    "snapshot_create",
                    "toggle_workspace_notifications",
                    "workspace_archive",
                ],
            }
        ],
    }

    assert output == expected


@pytest.mark.django_db
def test_user_get_all_permissions_empty():
    user = UserFactory()

    output = user.get_all_permissions()

    expected = {
        "global": [],
        "projects": [],
        "orgs": [],
    }
    assert output == expected


@pytest.mark.django_db
def test_user_get_all_roles():
    project = ProjectFactory()
    user = UserFactory(roles=[DataInvestigator])

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectCollaborator])

    output = user.get_all_roles()
    expected = {
        "global": ["DataInvestigator"],
        "orgs": [],
        "projects": [
            {
                "slug": project.slug,
                "roles": ["ProjectCollaborator"],
            }
        ],
    }

    assert output == expected


@pytest.mark.django_db
def test_user_get_all_roles_empty():
    user = UserFactory()

    output = user.get_all_roles()

    expected = {
        "global": [],
        "projects": [],
        "orgs": [],
    }
    assert output == expected


@pytest.mark.django_db
def test_user_is_unapproved_by_default():
    assert not UserFactory().is_approved


@pytest.mark.django_db
def test_userqueryset_success():
    user1 = UserFactory(roles=[CoreDeveloper, OutputChecker])
    user2 = UserFactory(roles=[OutputChecker])
    user3 = UserFactory(roles=[OutputPublisher])

    users = User.objects.filter_by_role(OutputChecker)

    assert user1 in users
    assert user2 in users
    assert user3 not in users


@pytest.mark.django_db
def test_userqueryset_unknown_role():
    with pytest.raises(Exception, match="Unknown Roles:.*"):
        User.objects.filter_by_role("unknown")


@pytest.mark.django_db
def test_workspace_get_absolute_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    url = workspace.get_absolute_url()

    assert url == reverse(
        "workspace-detail",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspace_get_releases_api_url():
    workspace = WorkspaceFactory()
    assert (
        workspace.get_releases_api_url()
        == f"/api/v2/releases/workspace/{workspace.name}"
    )


@pytest.mark.django_db
def test_workspace_get_archive_toggle_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    url = workspace.get_archive_toggle_url()

    assert url == reverse(
        "workspace-archive-toggle",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspace_get_files_url():
    workspace = WorkspaceFactory()

    url = workspace.get_files_url()

    assert url == reverse(
        "workspace-files-list",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspace_get_jobs_url():
    workspace = WorkspaceFactory()

    url = workspace.get_jobs_url()

    assert url == reverse(
        "job-request-create",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspace_get_latest_outputs_download_url():
    workspace = WorkspaceFactory()

    url = workspace.get_latest_outputs_download_url()

    assert url == reverse(
        "workspace-latest-outputs-download",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspace_get_latest_outputs_url():
    workspace = WorkspaceFactory()

    url = workspace.get_latest_outputs_url()

    assert url == reverse(
        "workspace-latest-outputs-detail",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspace_get_logs_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    url = workspace.get_logs_url()

    assert url == reverse(
        "workspace-logs",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspace_get_notifications_toggle_url():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    url = workspace.get_notifications_toggle_url()

    assert url == reverse(
        "workspace-notifications-toggle",
        kwargs={
            "org_slug": org.slug,
            "project_slug": project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspace_get_outputs_url():
    workspace = WorkspaceFactory()

    url = workspace.get_outputs_url()

    assert url == reverse(
        "workspace-output-list",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspace_get_releases_url():
    workspace = WorkspaceFactory()

    url = workspace.get_releases_url()

    assert url == reverse(
        "workspace-release-list",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


@pytest.mark.django_db
def test_workspace_get_statuses_url():
    workspace = WorkspaceFactory()
    url = workspace.get_statuses_url()
    assert url == reverse("api:workspace-statuses", kwargs={"name": workspace.name})


@pytest.mark.django_db
def test_workspace_get_action_status_lut_no_jobs():
    assert WorkspaceFactory().get_action_status_lut() == {}


@pytest.mark.django_db
def test_workspace_get_action_status_lut_with_backend():
    emis = Backend.objects.get(slug="emis")
    tpp = Backend.objects.get(slug="tpp")
    workspace1 = WorkspaceFactory()
    job_request = JobRequestFactory(backend=emis, workspace=workspace1)
    JobFactory(job_request=job_request, action="action1", status="pending")

    now = timezone.now()

    workspace2 = WorkspaceFactory()

    job_request1 = JobRequestFactory(backend=tpp, workspace=workspace2)
    # action1 (succeeded) & action2 (failure)
    JobFactory(
        job_request=job_request1,
        action="action1",
        status="succeeded",
        created_at=minutes_ago(now, 7),
    )
    JobFactory(
        job_request=job_request1,
        action="action2",
        status="failed",
        created_at=minutes_ago(now, 6),
    )

    job_request2 = JobRequestFactory(backend=tpp, workspace=workspace2)
    # action2 (succeeded) & action3 (failed)
    JobFactory(
        job_request=job_request2,
        action="action2",
        status="succeeded",
        created_at=minutes_ago(now, 5),
    )
    JobFactory(
        job_request=job_request2,
        action="action3",
        status="failed",
        created_at=minutes_ago(now, 4),
    )

    job_request3 = JobRequestFactory(backend=tpp, workspace=workspace2)
    # action2 (failed)
    JobFactory(
        job_request=job_request3,
        action="action2",
        status="failed",
        created_at=minutes_ago(now, 2),
    )

    job_request4 = JobRequestFactory(backend=tpp, workspace=workspace2)
    # action3 (succeeded) & action4 (failed)
    JobFactory(
        job_request=job_request4,
        action="action3",
        status="succeeded",
        created_at=minutes_ago(now, 2),
    )
    JobFactory(
        job_request=job_request4,
        action="action4",
        status="failed",
        created_at=minutes_ago(now, 1),
    )

    output = workspace2.get_action_status_lut(backend="tpp")
    expected = {
        "action1": "succeeded",
        "action2": "failed",
        "action3": "succeeded",
        "action4": "failed",
    }
    assert output == expected


@pytest.mark.django_db
def test_workspace_get_action_status_lut_without_backend():
    workspace1 = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace1)
    JobFactory(job_request=job_request, action="action1", status="pending")

    now = timezone.now()

    workspace2 = WorkspaceFactory()

    job_request1 = JobRequestFactory(workspace=workspace2)
    # action1 (succeeded) & action2 (failure)
    JobFactory(
        job_request=job_request1,
        action="action1",
        status="succeeded",
        created_at=minutes_ago(now, 7),
    )
    JobFactory(
        job_request=job_request1,
        action="action2",
        status="failed",
        created_at=minutes_ago(now, 6),
    )

    job_request2 = JobRequestFactory(workspace=workspace2)
    # action2 (succeeded) & action3 (failed)
    JobFactory(
        job_request=job_request2,
        action="action2",
        status="succeeded",
        created_at=minutes_ago(now, 5),
    )
    JobFactory(
        job_request=job_request2,
        action="action3",
        status="failed",
        created_at=minutes_ago(now, 4),
    )

    job_request3 = JobRequestFactory(workspace=workspace2)
    # action2 (failed)
    JobFactory(
        job_request=job_request3,
        action="action2",
        status="failed",
        created_at=minutes_ago(now, 2),
    )

    job_request4 = JobRequestFactory(workspace=workspace2)
    # action3 (succeeded) & action4 (failed)
    JobFactory(
        job_request=job_request4,
        action="action3",
        status="succeeded",
        created_at=minutes_ago(now, 2),
    )
    JobFactory(
        job_request=job_request4,
        action="action4",
        status="failed",
        created_at=minutes_ago(now, 1),
    )

    output = workspace2.get_action_status_lut()
    expected = {
        "action1": "succeeded",
        "action2": "failed",
        "action3": "succeeded",
        "action4": "failed",
    }
    assert output == expected


@pytest.mark.django_db
def test_workspace_repo_name_no_path():
    workspace = WorkspaceFactory(repo="http://example.com")

    with pytest.raises(Exception, match="not in expected format"):
        workspace.repo_name


@pytest.mark.django_db
def test_workspace_repo_name_success():
    workspace = WorkspaceFactory(repo="http://example.com/foo/test")
    assert workspace.repo_name == "test"


@pytest.mark.django_db
def test_workspace_repo_owner_no_path():
    workspace = WorkspaceFactory(repo="http://example.com")

    with pytest.raises(Exception, match="not in expected format"):
        workspace.repo_owner


@pytest.mark.django_db
def test_workspace_repo_owner_success():
    workspace = WorkspaceFactory(repo="http://example.com/foo/test")
    assert workspace.repo_owner == "foo"


@pytest.mark.django_db
def test_workspace_str():
    workspace = WorkspaceFactory(
        name="Corellian Engineering Corporation", repo="Corellia"
    )
    assert str(workspace) == "Corellian Engineering Corporation (Corellia)"
