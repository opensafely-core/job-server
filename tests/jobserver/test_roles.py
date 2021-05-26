from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser

from jobserver.roles import can_run_jobs

from ..factories import UserFactory


@pytest.mark.django_db
def test_can_run_jobs_with_authenticated_user_in_org():
    with patch("jobserver.roles.is_member_of_org", return_value=True):
        assert can_run_jobs(UserFactory())


@pytest.mark.django_db
def test_can_run_jobs_with_authenticated_user_not_in_org():
    with patch("jobserver.roles.is_member_of_org", return_value=False):
        assert not can_run_jobs(UserFactory())


@pytest.mark.django_db
def test_can_run_jobs_with_unauthenticated_user():
    with patch("jobserver.roles.is_member_of_org", return_value=False):
        assert not can_run_jobs(AnonymousUser())
