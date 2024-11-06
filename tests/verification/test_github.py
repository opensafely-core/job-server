import pytest
import stamina
from environs import Env
from requests.exceptions import HTTPError

from jobserver.github import GitHubAPI, RepoAlreadyExists, RepoNotYetCreated
from jobserver.models.common import new_ulid_str

from ..fakes import FakeGitHubAPI
from .utils import assert_deep_type_equality


pytestmark = [pytest.mark.verification, pytest.mark.disable_db]


@pytest.fixture
def clear_topics(github_api):
    args = [
        "opensafely-testing",
        "github-api-testing-topics",
        [],
    ]

    github_api.set_repo_topics(*args)

    try:
        yield
    finally:
        github_api.set_repo_topics(*args)


@pytest.fixture
def github_api():
    """create a new API instance so that we can use a separate token for these tests"""
    return GitHubAPI(token=Env().str("GITHUB_TOKEN_TESTING"))


def test_add_repo_to_team(enable_network, github_api):
    args = [
        "testing",
        "opensafely-testing",
        "github-api-testing-topics",
    ]

    assert github_api.add_repo_to_team(*args) is None
    assert FakeGitHubAPI().add_repo_to_team(*args) is None


def test_create_issue(enable_network, github_api):
    # use a private repo to test here so we can mirror what the output checkers
    # are doing
    args = [
        "opensafely-testing",
        "github-api-testing-private",
        "Test Issue",
        "test content",
        ["testing"],
    ]

    real = github_api.create_issue(*args)
    fake = FakeGitHubAPI().create_issue(*args)

    assert_deep_type_equality(fake, real)

    assert real is not None


def test_get_issue_number(enable_network, github_api):
    # use a private repo to test here so we can mirror what the output checkers
    # are doing
    args = ["opensafely-testing", "github-api-testing-private", "Test Issue"]

    real = github_api.get_issue_number_from_title(*args)
    fake = FakeGitHubAPI().get_issue_number_from_title(*args)
    assert_deep_type_equality(fake, real)

    assert real is not None


def test_get_issue_number_with_sort_order(enable_network, github_api):
    # use a private repo to test here so we can mirror what the output checkers
    # are doing
    args = ["opensafely-testing", "github-api-testing-private", "Test Issue"]

    default_order = github_api.get_issue_number_from_title(*args)
    latest = github_api.get_issue_number_from_title(*args, latest=True)
    oldest = github_api.get_issue_number_from_title(*args, latest=False)
    assert default_order == latest
    assert latest > oldest


def test_get_issue_number_no_matches(enable_network, github_api):
    args = ["opensafely-testing", "github-api-testing-private", new_ulid_str()]
    real = github_api.get_issue_number_from_title(*args)
    assert real is None


def test_create_issue_comment(enable_network, github_api):
    # use a private repo to test here so we can mirror what the output checkers
    # are doing
    # We assume there's at least one existing issue entitled "Test Issue"
    # (generated in previous test runs)
    args = [
        "opensafely-testing",
        "github-api-testing-private",
        "Test Issue",
        "A test comment",
    ]

    real = github_api.create_issue_comment(*args)
    fake = FakeGitHubAPI().create_issue_comment(*args)

    assert_deep_type_equality(fake, real)

    assert real is not None


@pytest.mark.parametrize("comment", [None, "Closed with reason"])
def test_close_issue(enable_network, github_api, comment):
    # use a private repo to test here so we can mirror what the output checkers
    # are doing
    # We assume there's at least one existing open issue entitled "Test Issue"
    # (generated in previous test runs)
    args = [
        "opensafely-testing",
        "github-api-testing-private",
        "Test Issue",
        comment,
        # Sort ascending, so we close the oldest one
        "asc",
    ]

    real = github_api.close_issue(*args)
    fake = FakeGitHubAPI().close_issue(*args)

    assert_deep_type_equality(fake, real)

    assert real is not None

    # reset the issue state
    github_api._change_issue_state(
        "opensafely-testing", "github-api-testing-private", real["number"], "open"
    )


def test_create_repo(enable_network, github_api):
    try:
        # create a unique ID for this test using our existing ULID function.
        # we can have multiple CI runs executing concurrently which means this
        # test can be running in different CI jobs at the same time.  Given the
        # test talks to an external API we can't use the same repo name for every
        # execution.  Instead we use our new_ulid_str since it's already available
        # and should have more than enough uniqueness for our needs to create
        # a unique repo name.
        unique_id = new_ulid_str()
        args = [
            "opensafely-testing",
            f"testing-create_repo-{unique_id}",
        ]

        real = github_api.create_repo(*args)
        fake = FakeGitHubAPI().create_repo(*args)

        assert_deep_type_equality(fake, real)

        assert real is not None

        # do we get the appropriate error when the repo already exists?
        with pytest.raises(RepoAlreadyExists):
            github_api.create_repo(*args)
    finally:
        # clean up after the test but accept that sometimes the repo hasn't
        # been created and make a few attempts at removing it
        for attempt in stamina.retry_context(on=RepoNotYetCreated):
            with attempt:
                github_api.delete_repo(*args)


def test_get_branch(enable_network, github_api):
    args = ["opensafely-testing", "github-api-testing", "main"]

    real = github_api.get_branch(*args)
    fake = FakeGitHubAPI().get_branch(*args)

    assert_deep_type_equality(fake, real)

    assert real is not None


def test_get_branch_with_missing_branch(enable_network, github_api):
    assert github_api.get_branch("opensafely-testing", "some_repo", "missing") is None


def test_get_branches(enable_network, github_api):
    args = ["opensafely-testing", "github-api-testing"]

    real = github_api.get_branches(*args)
    fake = FakeGitHubAPI().get_branches(*args)

    assert_deep_type_equality(fake, real)

    assert real is not None


def test_get_branches_with_unknown_org(enable_network, github_api):
    args = ["opensafely-not-real", "github-api-testing"]

    real = github_api.get_branches(*args)
    fake = FakeGitHubAPI().get_branches(*args)

    assert_deep_type_equality(fake, real)

    assert real == []


def test_get_branches_with_unknown_repo(enable_network, github_api):
    args = ["opensafely-testing", "github-api-not-real"]

    real = github_api.get_branches(*args)
    fake = FakeGitHubAPI().get_branches(*args)

    assert_deep_type_equality(fake, real)

    assert real == []


def test_get_branch_sha(enable_network, github_api):
    args = ["opensafely-testing", "github-api-testing", "test-get_branch_sha"]

    real = github_api.get_branch_sha(*args)
    fake = FakeGitHubAPI().get_branch_sha(*args)

    assert real == "71650d527c9288f90aa01d089f5a9884b683f7ed"

    # get_branch_sha is a wrapper for get_branch to extract just the SHA as a
    # string so no need to throw assert_deep_type_equality() at it
    assert isinstance(fake, str)


def test_get_tag_sha(enable_network, github_api):
    args = ["opensafely-testing", "github-api-testing", "test-tag"]

    real = github_api.get_tag_sha(*args)
    fake = FakeGitHubAPI().get_tag_sha(*args)

    assert real == "7c48e4e81db5fe932628cd92f51c7858759d6b98"

    assert isinstance(fake, str)


def test_get_branch_sha_with_missing_branch(enable_network, github_api):
    sha = github_api.get_branch_sha(
        "opensafely-testing",
        "some_repo",
        "missing",
    )

    assert sha is None


def test_get_default_file(enable_network, github_api):
    args = ["opensafely-testing", "github-api-testing", "main"]

    real = github_api.get_file(*args)
    fake = FakeGitHubAPI().get_file(*args)

    assert_deep_type_equality(fake, real)


def test_get_file(enable_network, github_api):
    args = ["opensafely-testing", "github-api-testing", "main"]

    real = github_api.get_file(*args)
    fake = FakeGitHubAPI().get_file(*args, filepath="README.md")

    assert_deep_type_equality(fake, real)


def test_get_file_missing_project_yml(enable_network, github_api):
    output = github_api.get_file(
        "opensafely-testing",
        "github-api-testing",
        "missing_project",
    )

    assert output is None


def test_get_repo(enable_network, github_api):
    args = ["opensafely-testing", "github-api-testing"]

    real = github_api.get_repo(*args)
    fake = FakeGitHubAPI().get_repo(*args)

    assert_deep_type_equality(fake, real)


def test_get_repo_is_private(enable_network, github_api):
    args = ["opensafely-testing", "github-api-testing-private"]

    assert github_api.get_repo_is_private(*args)
    assert FakeGitHubAPI().get_repo_is_private(*args)


def test_get_repo_is_private_with_unknown_repo(enable_network, github_api):
    assert github_api.get_repo_is_private("opensafely-testing", "unknown") is None


def test_get_repo_with_unknown_repo(enable_network, github_api):
    assert github_api.get_repo("opensafely-testing", "unknown") is None


def test_get_repos_with_branches(enable_network, github_api):
    args = ["opensafely-testing"]

    real = list(github_api.get_repos_with_branches(*args))
    fake = FakeGitHubAPI().get_repos_with_branches(*args)

    assert_deep_type_equality(fake, real)


def test_get_repos_with_dates(enable_network, github_api):
    args = ["opensafely-testing"]

    real = list(github_api.get_repos_with_dates(*args))
    fake = FakeGitHubAPI().get_repos_with_dates(*args)

    assert_deep_type_equality(fake, real)


def test_get_repos_with_status_and_url(enable_network, github_api):
    args = ["opensafely-testing"]

    real = list(github_api.get_repos_with_status_and_url(args))
    fake = FakeGitHubAPI().get_repos_with_status_and_url(args)

    assert_deep_type_equality(fake, real)


def test_graphql_error_handling(enable_network, github_api):
    """
    Are we raising errors around unexpected GraphQL responses?

    Some GraphQL responses, typically to malformed queries, don't return a
    `data` key in their response.
    """
    query = """
    query {
      viewer {
        not_a_real_field
      }
    }
    """

    with pytest.raises(RuntimeError):
        list(github_api._iter_query_results(query))


def test_set_repo_topics(enable_network, github_api, clear_topics):
    args = [
        "opensafely-testing",
        "github-api-testing-topics",
        ["testing"],
    ]

    real = github_api.set_repo_topics(*args)
    fake = FakeGitHubAPI().set_repo_topics(*args)

    assert_deep_type_equality(fake, real)

    assert real is not None

    repo = github_api.get_repo("opensafely-testing", "github-api-testing-topics")
    assert repo["topics"] == ["testing"]


def test_unauthenticated_request(enable_network):
    try:
        assert GitHubAPI().get_repo("opensafely-testing", "github-api-testing")
    except HTTPError as e:  # pragma: no cover
        forbidden = e.response.status_code == 403
        rate_limited = "rate limit exceeded for url" in str(e)

        if forbidden and rate_limited:
            # being rate limited is still a valid access of the API
            assert True
        else:
            raise
