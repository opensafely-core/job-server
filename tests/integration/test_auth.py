import responses
from django.urls import reverse
from furl import furl

from jobserver.models import User


def test_login_pipeline(client, slack_messages):
    """
    Test the Auth Pipeline with an incoming request

    When the Auth provider (GitHub) redirects back to us we make various
    requests (for extra data) to GitHub to construct a User.  This test checks,
    given an incoming URL and subsequent payloads constructed from real
    requests that we end up with a User in the expected state.
    """
    assert User.objects.count() == 0

    # mock the various GitHub URLs the Python/Django Social Auth Pipeline talks
    # to when constructing a User
    with responses.RequestsMock() as rsps:
        access_token_url = "https://github.com/login/oauth/access_token"
        access_token_data = {
            "access_token": "dummy-token",
            "token_type": "bearer",
            "scope": "user:email",
        }
        rsps.add(responses.POST, access_token_url, json=access_token_data, status=200)

        user_url = "https://api.github.com/user"
        user_data = {
            "id": "1234",
            "login": "dummy-user",
            "name": "Test User",
            "email": None,
        }
        rsps.add(responses.GET, user_url, json=user_data, status=200)

        emails_url = "https://api.github.com/user/emails"
        emails_data = [
            {
                "email": "test@example.com",
                "primary": True,
                "verified": True,
                "visibility": "private",
            },
        ]
        rsps.add(responses.GET, emails_url, json=emails_data, status=200)

        # set a dummy state value in the test Client's session to match the
        # value in redirect_url below
        session = client.session
        session["github_state"] = "test-state"
        session.save()

        # construct the URL path we've configured our GitHub OAuth application
        # with, and set the expected query args.  Code is unused in this case
        # (it would be constructed on our side from the Client ID/Secret when
        # we redirected out to GitHub).  State would be sent by GitHub (also
        # built using the known Client ID/Secret & Code we sent) and then
        # matched against the state value we had constructed in the same way
        # locally and stored in the session.
        redirect_url = (
            reverse("social:complete", kwargs={"backend": "github"})
            + "?code=test-code&state=test-state"
        )

        response = client.get(redirect_url, follow=False, secure=True)

    assert response.status_code == 302
    assert response.url == "/"

    # ensure we only have one User and it's constructed as expected
    assert User.objects.count() == 1
    user = User.objects.first()
    assert user.fullname == "Test User"
    assert user.email == "test@example.com"
    assert user.is_active
    assert not user.is_staff
    assert user.roles == []


def test_login_pipeline_without_gitub_token(client, slack_messages):
    """
    Test the Auth Pipeline with an incoming request but no GitHub API access

    When the Auth provider (GitHub) redirects back to us we make various
    requests (for extra data) to GitHub to construct a User.  This test checks,
    given an incoming URL and subsequent payloads constructed from real
    requests, that we handle a lack of access to GitHub's API.
    """
    assert User.objects.count() == 0

    # mock the various GitHub URLs the Python/Django Social Auth Pipeline talks
    # to when constructing a User
    with responses.RequestsMock() as rsps:
        access_token_url = "https://github.com/login/oauth/access_token"
        access_token_data = {
            "access_token": "dummy-token",
            "token_type": "bearer",
            "scope": "user:email",
        }
        rsps.add(responses.POST, access_token_url, json=access_token_data, status=200)

        user_url = "https://api.github.com/user"
        user_data = {
            "id": "1234",
            "login": "dummy-user",
            "name": "Test User",
            "email": None,
        }
        rsps.add(responses.GET, user_url, json=user_data, status=200)

        emails_url = "https://api.github.com/user/emails"
        emails_data = [
            {
                "email": "test@example.com",
                "primary": True,
                "verified": True,
                "visibility": "private",
            },
        ]
        rsps.add(responses.GET, emails_url, json=emails_data, status=200)

        # set a dummy state value in the test Client's session to match the
        # value in redirect_url below
        session = client.session
        session["github_state"] = "test-state"
        session.save()

        # construct the URL path we've configured our GitHub OAuth application
        # with, and set the expected query args.  Code is unused in this case
        # (it would be constructed on our side from the Client ID/Secret when
        # we redirected out to GitHub).  State would be sent by GitHub (also
        # built using the known Client ID/Secret & Code we sent) and then
        # matched against the state value we had constructed in the same way
        # locally and stored in the session.
        redirect_url = (
            reverse("social:complete", kwargs={"backend": "github"})
            + "?code=test-code&state=test-state"
        )

        response = client.get(redirect_url, follow=False, secure=True)

    assert response.status_code == 302
    assert response.url == "/"


def test_login_redirects_correctly(client):
    login_url = reverse("auth-login", kwargs={"backend": "github"})
    response = client.post(login_url)

    assert response.status_code == 302

    f = furl(response.url)
    assert f.scheme == "https"
    assert f.host == "github.com"
    assert str(f.path) == "/login/oauth/authorize"
    assert f.args["client_id"] == "test"  # configured in pyproject.toml
    assert "state" in f.args  # dynamically generated by the Auth Backend
    assert f.args["redirect_uri"] == "http://testserver/complete/github/"
    assert f.args["scope"] == "user:email"


def test_login_with_get_request_fails(client):
    login_url = reverse("auth-login", kwargs={"backend": "github"})
    response = client.get(login_url)

    assert response.status_code == 405
