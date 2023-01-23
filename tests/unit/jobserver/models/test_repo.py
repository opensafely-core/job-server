import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from ....factories import RepoFactory, UserFactory


def test_repo_constraints_internal_signed_off_at_and_internal_signed_off_by_both_set():
    RepoFactory(
        internal_signed_off_at=timezone.now(), internal_signed_off_by=UserFactory()
    )


def test_repo_constraints_internal_signed_off_at_and_internal_signed_off_by_neither_set():
    RepoFactory(internal_signed_off_at=None, internal_signed_off_by=None)


@pytest.mark.django_db(transaction=True)
def test_repo_constraints_missing_internal_signed_off_at_or_internal_signed_off_by():
    with pytest.raises(IntegrityError):
        RepoFactory(internal_signed_off_at=None, internal_signed_off_by=UserFactory())

    with pytest.raises(IntegrityError):
        RepoFactory(internal_signed_off_at=timezone.now(), internal_signed_off_by=None)


def test_repo_constraints_researcher_signed_off_at_and_researcher_signed_off_by_both_set():
    RepoFactory(
        researcher_signed_off_at=timezone.now(), researcher_signed_off_by=UserFactory()
    )


def test_repo_constraints_researcher_signed_off_at_and_researcher_signed_off_by_neither_set():
    RepoFactory(researcher_signed_off_at=None, researcher_signed_off_by=None)


@pytest.mark.django_db(transaction=True)
def test_repo_constraints_missing_researcher_signed_off_at_or_researcher_signed_off_by():
    with pytest.raises(IntegrityError):
        RepoFactory(
            researcher_signed_off_at=None, researcher_signed_off_by=UserFactory()
        )

    with pytest.raises(IntegrityError):
        RepoFactory(
            researcher_signed_off_at=timezone.now(), researcher_signed_off_by=None
        )


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
