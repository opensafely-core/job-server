from datetime import timedelta

import pytest
from django.db import IntegrityError
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
from jobserver.models import JobRequest, User

from ....factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)
from ....utils import minutes_ago, seconds_ago


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


def test_job_is_missing_updates_above_threshold():
    last_update = minutes_ago(timezone.now(), 50)
    job = JobFactory(completed_at=None, updated_at=last_update)

    assert job.is_missing_updates


def test_job_is_missing_updates_below_threshold():
    last_update = minutes_ago(timezone.now(), 29)
    job = JobFactory(completed_at=None, updated_at=last_update)

    assert not job.is_missing_updates


def test_job_is_missing_updates_missing_updated_at():
    assert not JobFactory(status="pending", updated_at=None).is_missing_updates


def test_job_is_missing_updates_completed():
    assert not JobFactory(status="failed").is_missing_updates


def test_job_run_command_empty_project_definition():
    job_request = JobRequestFactory(project_definition="")

    assert JobFactory(job_request=job_request).run_command is None


def test_job_run_command_success():
    pipeline = """
    version: 3.0
    expectations:
      population_size: 1000
    actions:
      my_action:
        run: cowsay research!
        outputs:
          moderately_sensitive:
            log: logs/cowsay.log
    """

    job_request = JobRequestFactory(project_definition=pipeline)
    job = JobFactory(job_request=job_request, action="my_action")

    assert job.run_command == "cowsay research!"


def test_job_runtime():
    duration = timedelta(hours=1, minutes=2, seconds=3)
    started_at = timezone.now() - duration
    job = JobFactory(
        status="succeeded", started_at=started_at, completed_at=timezone.now()
    )

    assert job.runtime.hours == 1
    assert job.runtime.minutes == 2
    assert job.runtime.seconds == 3


def test_job_runtime_not_completed():
    job = JobFactory(status="running", started_at=timezone.now())

    # an uncompleted job has no runtime
    assert not job.runtime


def test_job_runtime_not_started():
    job = JobFactory(status="pending")

    # an unstarted job has no runtime
    assert not job.runtime


def test_job_runtime_without_timestamps():
    job = JobFactory(status="succeeded", started_at=None, completed_at=None)

    assert not job.runtime


def test_job_str():
    job = JobFactory(action="Run")

    assert str(job) == f"Run ({job.pk})"


def test_jobrequest_completed_at_no_jobs():
    assert not JobRequestFactory().completed_at


def test_jobrequest_completed_at_success():
    test_completed_at = timezone.now()

    job_request = JobRequestFactory()

    JobFactory(
        job_request=job_request,
        status="succeeded",
        completed_at=(test_completed_at - timedelta(minutes=1)),
    )
    job2 = JobFactory(
        job_request=job_request, status="succeeded", completed_at=test_completed_at
    )

    jr = JobRequest.objects.get(pk=job_request.pk)

    assert jr.completed_at == test_completed_at
    assert jr.completed_at == job2.completed_at


def test_jobrequest_completed_at_while_incomplete():
    job_request = JobRequestFactory()

    JobFactory(job_request=job_request, completed_at=timezone.now())
    JobFactory(job_request=job_request)

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert not jr.completed_at


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


def test_jobrequest_get_project_yaml_url_no_sha():
    repo = RepoFactory(url="http://example.com/opensafely/some_repo")
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace)

    url = job_request.get_file_url("test-blah.foo")

    assert url == "http://example.com/opensafely/some_repo"


def test_jobrequest_get_project_yaml_url_success():
    repo = RepoFactory(url="http://example.com/opensafely/some_repo")
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace, sha="abc123")

    url = job_request.get_file_url("test-blah.foo")

    assert url == "http://example.com/opensafely/some_repo/blob/abc123/test-blah.foo"


def test_jobrequest_get_repo_url_no_sha():
    repo = RepoFactory(url="http://example.com/opensafely/some_repo")
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace)

    url = job_request.get_repo_url()

    assert url == "http://example.com/opensafely/some_repo"


def test_jobrequest_get_repo_url_success():
    repo = RepoFactory(url="http://example.com/opensafely/some_repo")
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace, sha="abc123")

    url = job_request.get_repo_url()

    assert url == "http://example.com/opensafely/some_repo/tree/abc123"


def test_jobrequest_is_completed():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.is_completed


def test_jobrequest_is_invalid():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, action="__error__")

    assert job_request.is_invalid


def test_jobrequest_num_completed_no_jobs():
    assert JobRequestFactory().num_completed == 0


def test_job_request_num_completed_success():
    job_request = JobRequestFactory()

    job1, job2 = JobFactory.create_batch(2, job_request=job_request, status="succeeded")

    assert job_request.num_completed == 2


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

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.started_at
    assert not jr.completed_at

    # combined _completed_ Job runtime is 0 because the failed job has no
    # runtime (it never started)
    assert jr.runtime
    assert jr.runtime.hours == 0
    assert jr.runtime.minutes == 1
    assert jr.runtime.seconds == 0


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

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.started_at
    assert jr.completed_at

    # combined _completed_ Job runtime is 2 minutes because the second job
    # failed before it started
    assert jr.runtime
    assert jr.runtime.hours == 0
    assert jr.runtime.minutes == 2
    assert jr.runtime.seconds == 0


def test_jobrequest_runtime_no_jobs():
    JobRequestFactory()
    assert not JobRequest.objects.first().runtime


def test_jobrequest_runtime_not_completed(freezer):
    jr = JobRequestFactory()

    now = timezone.now()

    JobFactory(
        job_request=jr,
        status="succeeded",
        started_at=minutes_ago(now, 2),
        completed_at=minutes_ago(now, 1),
    )
    JobFactory(
        job_request=jr,
        status="running",
        started_at=seconds_ago(now, 30),
    )

    job_request = JobRequest.objects.first()
    assert job_request.started_at
    assert not job_request.completed_at

    # combined _completed_ Job runtime is 1 minute
    assert job_request.runtime
    assert job_request.runtime.hours == 0
    assert job_request.runtime.minutes == 1
    assert job_request.runtime.seconds == 0


def test_jobrequest_runtime_not_started():
    jr = JobRequestFactory()

    JobFactory(job_request=jr, status="running")
    JobFactory(job_request=jr, status="pending")

    assert not JobRequest.objects.first().runtime


def test_jobrequest_runtime_success():
    jr = JobRequestFactory()

    start = timezone.now() - timedelta(hours=1)

    JobFactory(
        job_request=jr,
        status="succeeded",
        started_at=start,
        completed_at=start + timedelta(minutes=1),
    )
    JobFactory(
        job_request=jr,
        status="failed",
        started_at=start + timedelta(minutes=2),
        completed_at=start + timedelta(minutes=3),
    )

    job_request = JobRequest.objects.first()
    assert job_request.runtime
    assert job_request.runtime.hours == 0
    assert job_request.runtime.minutes == 2
    assert job_request.runtime.seconds == 0


@pytest.mark.parametrize(
    "statuses,expected",
    [
        (["failed", "failed", "failed", "failed"], "failed"),
        (["pending", "pending", "pending", "pending"], "pending"),
        (["running", "running", "running", "running"], "running"),
        (["succeeded", "succeeded", "succeeded", "succeeded"], "succeeded"),
    ],
)
def test_jobrequest_status_all_jobs_the_same(statuses, expected):
    job_request = JobRequestFactory()
    for status in statuses:
        JobFactory(job_request=job_request, status=status)

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.status == expected


def test_jobrequest_status_running_in_job_statuses():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="running")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.status == "running"


def test_jobrequest_status_running_not_in_job_statues():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.status == "running"


def test_jobrequest_status_failed():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.status == "failed"


def test_jobrequest_status_unknown():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="foo")
    JobFactory(job_request=job_request, status="bar")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.status == "unknown"


def test_jobrequest_status_uses_prefetch_cache(django_assert_num_queries):
    for i in range(5):
        jr = JobRequestFactory()
        JobFactory.create_batch(5, job_request=jr)

    with django_assert_num_queries(2):
        # 1. select JobRequests
        # 2. select Jobs for those JobRequests
        [jr.status for jr in JobRequest.objects.all()]


def test_jobrequest_status_without_prefetching_jobs(django_assert_num_queries):
    job_request = JobRequestFactory()
    JobFactory.create_batch(5, job_request=job_request)

    with pytest.raises(Exception, match="JobRequest queries must prefetch jobs."):
        job_request.status


def test_org_default_for_github_orgs():
    org1 = OrgFactory()
    assert org1.github_orgs == ["opensafely"]

    org2 = OrgFactory()
    assert org2.github_orgs == ["opensafely"]

    # does mutating the field affect the other object?
    org1.github_orgs += ["test"]
    org1.save()
    org1.refresh_from_db()

    assert org1.github_orgs == ["opensafely", "test"]
    assert org2.github_orgs == ["opensafely"]


def test_org_get_absolute_url():
    org = OrgFactory()
    url = org.get_absolute_url()
    assert url == reverse("org-detail", kwargs={"org_slug": org.slug})


def test_org_get_edit_url():
    org = OrgFactory()

    url = org.get_edit_url()

    assert url == reverse("staff:org-edit", kwargs={"slug": org.slug})


def test_org_get_staff_url():
    org = OrgFactory()

    url = org.get_staff_url()

    assert url == reverse("staff:org-detail", kwargs={"slug": org.slug})


def test_org_populates_slug():
    assert OrgFactory(name="Test Org", slug="").slug == "test-org"


def test_org_str():
    assert str(OrgFactory(name="Test Org")) == "Test Org"


def test_orgmembership_str():
    org = OrgFactory(name="EBMDataLab")
    user = UserFactory(username="ben")

    membership = OrgMembershipFactory(org=org, user=user)

    assert str(membership) == "ben | EBMDataLab"


def test_project_get_absolute_url():
    org = OrgFactory(name="test-org")
    project = ProjectFactory(org=org)
    url = project.get_absolute_url()
    assert url == reverse(
        "project-detail", kwargs={"org_slug": org.slug, "project_slug": project.slug}
    )


def test_project_get_approved_url_with_number():
    project = ProjectFactory(number=42)

    assert (
        project.get_approved_url()
        == "https://www.opensafely.org/approved-projects#project-42"
    )


def test_project_get_approved_url_without_number():
    project = ProjectFactory()

    assert project.get_approved_url() == "https://www.opensafely.org/approved-projects"


def test_project_get_edit_url():
    project = ProjectFactory()

    url = project.get_edit_url()

    assert url == reverse(
        "project-edit",
        kwargs={"org_slug": project.org.slug, "project_slug": project.slug},
    )


def test_project_get_staff_edit_url():
    project = ProjectFactory()

    url = project.get_staff_edit_url()

    assert url == reverse("staff:project-edit", kwargs={"slug": project.slug})


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


def test_project_get_staff_url():
    project = ProjectFactory()

    url = project.get_staff_url()

    assert url == reverse("staff:project-detail", kwargs={"slug": project.slug})


def test_project_get_staff_feature_flags_url():
    project = ProjectFactory()

    url = project.get_staff_feature_flags_url()

    assert url == reverse("staff:project-feature-flags", kwargs={"slug": project.slug})


def test_project_populates_slug():
    assert ProjectFactory(name="Test Project", slug="").slug == "test-project"


def test_project_str():
    project = ProjectFactory(
        org=OrgFactory(name="test-org"),
        name="Very Good Project",
    )
    assert str(project) == "test-org | Very Good Project"


def test_project_title():
    project = ProjectFactory(number=None)
    assert project.title == project.name

    project = ProjectFactory(name="test", number=123)
    assert project.title == "123 - test"


def test_projectmembership_get_staff_edit_url():
    project = ProjectFactory()
    membership = ProjectMembershipFactory(project=project)

    url = membership.get_staff_edit_url()

    assert url == reverse(
        "staff:project-membership-edit",
        kwargs={
            "slug": project.slug,
            "pk": membership.pk,
        },
    )


def test_projectmembership_get_staff_remove_url():
    project = ProjectFactory()
    membership = ProjectMembershipFactory(project=project)

    url = membership.get_staff_remove_url()

    assert url == reverse(
        "staff:project-membership-remove",
        kwargs={
            "slug": project.slug,
            "pk": membership.pk,
        },
    )


def test_projectmembership_str():
    project = ProjectFactory(name="DataLab")
    user = UserFactory(username="ben")

    membership = ProjectMembershipFactory(project=project, user=user)

    assert str(membership) == "ben | DataLab"


def test_repo_get_handler_url():
    repo = RepoFactory()

    url = repo.get_handler_url()

    assert url == reverse("repo-handler", kwargs={"repo_url": repo.quoted_url})


def test_repo_get_sign_off_url():
    repo = RepoFactory()

    url = repo.get_sign_off_url()

    assert url == reverse(
        "repo-sign-off",
        kwargs={"repo_url": repo.quoted_url},
    )


def test_repo_get_staff_sign_off_url():
    repo = RepoFactory()

    url = repo.get_staff_sign_off_url()

    assert url == reverse(
        "staff:repo-sign-off",
        kwargs={"repo_url": repo.quoted_url},
    )


def test_repo_get_staff_url():
    repo = RepoFactory()

    url = repo.get_staff_url()

    assert url == reverse("staff:repo-detail", kwargs={"repo_url": repo.quoted_url})


def test_repo_name_no_path():
    with pytest.raises(Exception, match="not in expected format"):
        RepoFactory(url="http://example.com").name


def test_repo_name_success():
    assert RepoFactory(url="http://example.com/foo/test").name == "test"


def test_repo_owner_no_path():
    with pytest.raises(Exception, match="not in expected format"):
        RepoFactory(url="http://example.com").owner


def test_repo_owner_success():
    assert RepoFactory(url="http://example.com/foo/test").owner == "foo"


def test_repo_str():
    assert str(RepoFactory(url="test")) == "test"


def test_user_constraints_pat_token_and_pat_expires_at_both_set():
    UserFactory(pat_token="test", pat_expires_at=timezone.now())


def test_user_constraints_pat_token_and_pat_expires_at_neither_set():
    UserFactory(pat_token=None, pat_expires_at=None)


@pytest.mark.django_db(transaction=True)
def test_user_constraints_missing_pat_token_or_pat_expires_at():
    with pytest.raises(IntegrityError):
        UserFactory(pat_token=None, pat_expires_at=timezone.now())

    with pytest.raises(IntegrityError):
        UserFactory(pat_token="test", pat_expires_at=None)


def test_user_name():
    assert UserFactory(fullname="first last", username="test").name == "first last"
    assert UserFactory(username="username").name == "username"


def test_user_get_all_permissions():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    user = UserFactory(roles=[CoreDeveloper])

    OrgMembershipFactory(org=org, user=user, roles=[OrgCoordinator])
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    output = user.get_all_permissions()
    expected = {
        "global": [
            "application_manage",
            "backend_manage",
            "org_create",
            "user_manage",
        ],
        "orgs": [{"slug": org.slug, "permissions": []}],
        "projects": [
            {
                "slug": project.slug,
                "permissions": [
                    "job_cancel",
                    "job_run",
                    "snapshot_create",
                    "unreleased_outputs_view",
                    "workspace_archive",
                    "workspace_create",
                    "workspace_toggle_notifications",
                ],
            }
        ],
    }

    assert output == expected


def test_user_get_all_permissions_empty():
    user = UserFactory()

    output = user.get_all_permissions()

    expected = {
        "global": [],
        "projects": [],
        "orgs": [],
    }
    assert output == expected


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


def test_user_get_all_roles_empty():
    user = UserFactory()

    output = user.get_all_roles()

    expected = {
        "global": [],
        "projects": [],
        "orgs": [],
    }
    assert output == expected


def test_user_get_staff_url():
    user = UserFactory()

    url = user.get_staff_url()

    assert url == reverse(
        "staff:user-detail",
        kwargs={
            "username": user.username,
        },
    )


def test_user_is_unapproved_by_default():
    assert not UserFactory().is_approved


def test_user_rotate_token(freezer):
    user = UserFactory()

    assert user.pat_token is None
    assert user.pat_expires_at is None

    # shift time to a date in the past
    freezer.move_to("2022-04-07")

    # set the user's pat_token and pat_expires_at
    token = user.rotate_token()

    # check the unhashed token has the pat_expires_at included
    assert token.endswith(user.pat_expires_at.date().isoformat())

    expires_at1 = user.pat_expires_at
    token1 = user.pat_token

    assert expires_at1
    assert token1

    # shift time forward a couple of days and update pat_* fields
    freezer.move_to("2022-04-09")
    user.rotate_token()

    assert user.pat_expires_at > expires_at1
    assert user.pat_token != token1


def test_user_valid_pat_success():
    user = UserFactory()
    token = user.rotate_token()

    assert user.has_valid_pat(token)


def test_user_valid_pat_with_empty_token():
    user = UserFactory()

    assert not user.has_valid_pat("")
    assert not user.has_valid_pat(None)


def test_user_valid_pat_with_expired_token(freezer):
    user = UserFactory()
    token = user.rotate_token()
    user.pat_expires_at = timezone.now() - timedelta(days=1)
    user.save()

    assert not user.has_valid_pat(token)


def test_user_valid_pat_with_invalid_token():
    user = UserFactory()
    user.rotate_token()

    assert not user.has_valid_pat("invalid")


def test_userqueryset_success():
    user1 = UserFactory(roles=[CoreDeveloper, OutputChecker])
    user2 = UserFactory(roles=[OutputChecker])
    user3 = UserFactory(roles=[OutputPublisher])

    users = User.objects.filter_by_role(OutputChecker)

    assert user1 in users
    assert user2 in users
    assert user3 not in users


def test_userqueryset_unknown_role():
    with pytest.raises(Exception, match="Unknown Roles:.*"):
        User.objects.filter_by_role("unknown")


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


def test_workspace_get_releases_api_url():
    workspace = WorkspaceFactory()
    assert (
        workspace.get_releases_api_url()
        == f"/api/v2/releases/workspace/{workspace.name}"
    )


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


def test_workspace_get_edit_url():
    workspace = WorkspaceFactory()

    url = workspace.get_edit_url()

    assert url == reverse(
        "workspace-edit",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


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


def test_workspace_get_pick_ref_url():
    workspace = WorkspaceFactory()

    url = workspace.get_pick_ref_url()

    assert url == reverse(
        "job-request-pick-ref",
        kwargs={
            "org_slug": workspace.project.org.slug,
            "project_slug": workspace.project.slug,
            "workspace_slug": workspace.name,
        },
    )


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


def test_workspace_get_statuses_url():
    workspace = WorkspaceFactory()
    url = workspace.get_statuses_url()
    assert url == reverse("api:workspace-statuses", kwargs={"name": workspace.name})


def test_workspace_get_staff_url():
    workspace = WorkspaceFactory()

    url = workspace.get_staff_url()

    assert url == reverse("staff:workspace-detail", kwargs={"slug": workspace.name})


def test_workspace_get_staff_edit_url():
    workspace = WorkspaceFactory()

    url = workspace.get_staff_edit_url()

    assert url == reverse("staff:workspace-edit", kwargs={"slug": workspace.name})


def test_workspace_get_action_status_lut_no_jobs():
    assert WorkspaceFactory().get_action_status_lut() == {}


def test_workspace_get_action_status_lut_with_backend():
    workspace1 = WorkspaceFactory()
    job_request = JobRequestFactory(backend=BackendFactory(), workspace=workspace1)
    JobFactory(job_request=job_request, action="action1", status="pending")

    now = timezone.now()

    backend = BackendFactory()
    workspace2 = WorkspaceFactory()

    job_request1 = JobRequestFactory(backend=backend, workspace=workspace2)
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

    job_request2 = JobRequestFactory(backend=backend, workspace=workspace2)
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

    job_request3 = JobRequestFactory(backend=backend, workspace=workspace2)
    # action2 (failed)
    JobFactory(
        job_request=job_request3,
        action="action2",
        status="failed",
        created_at=minutes_ago(now, 2),
    )

    job_request4 = JobRequestFactory(backend=backend, workspace=workspace2)
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

    output = workspace2.get_action_status_lut(backend=backend.slug)
    expected = {
        "action1": "succeeded",
        "action2": "failed",
        "action3": "succeeded",
        "action4": "failed",
    }
    assert output == expected


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


def test_workspace_str():
    repo = RepoFactory(url="Corellia")
    workspace = WorkspaceFactory(name="Corellian Engineering Corporation", repo=repo)

    assert str(workspace) == "Corellian Engineering Corporation (Corellia)"
