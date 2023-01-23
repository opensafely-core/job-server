import pytest
from django.urls import reverse

from ....factories import RepoFactory


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
