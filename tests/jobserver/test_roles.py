import pytest
from django.contrib.auth.models import AnonymousUser

from jobserver.roles import can_run_jobs

from ..factories import UserFactory


@pytest.mark.django_db
def test_can_run_jobs_with_authenticated_user_in_org(user, mocker):
    mocker.patch("jobserver.roles.is_member_of_org", return_value=True)

    assert can_run_jobs(user)


@pytest.mark.django_db
def test_can_run_jobs_with_authenticated_user_not_in_gh_org(user, mocker):
    mocker.patch("jobserver.roles.is_member_of_org", return_value=False)

    assert not can_run_jobs(user)


@pytest.mark.django_db
def test_can_run_jobs_with_authenticated_user_not_in_os_org():
    assert not can_run_jobs(UserFactory())


@pytest.mark.django_db
def test_can_run_jobs_with_unauthenticated_user(mocker):
    mocker.patch("jobserver.roles.is_member_of_org", return_value=False)

    assert not can_run_jobs(AnonymousUser())
