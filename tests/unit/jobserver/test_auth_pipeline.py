import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.urls import reverse
from social_core.backends.github import GithubOAuth2
from social_django.models import DjangoStorage
from social_django.strategy import DjangoStrategy

from jobserver.auth_pipeline import pipeline

from ...factories import UserFactory, UserSocialAuthFactory


@pytest.fixture
def strategy():
    return DjangoStrategy(storage=DjangoStorage())


def test_pipeline_with_existing_social_user(strategy):
    backend = GithubOAuth2(strategy=strategy)
    user = UserFactory(username="dummy-user")
    UserSocialAuthFactory(user=user, uid="1234")

    response = {
        "id": "1234",
        "login": "dummy-user",
        "name": "Test User",
        "email": "test@example.com",
        "access_token": "sekret",
        "token_type": "bearer",
    }
    output = pipeline(
        backend=backend,
        pipeline_index=0,
        strategy=strategy,
        response=response,
    )

    assert output["user"].username == "dummy-user"


def test_pipeline_with_existing_non_social_user(slack_messages, strategy):
    backend = GithubOAuth2(strategy=strategy)
    UserFactory(username="dummy-user")

    response = {
        "id": "1234",
        "login": "dummy-user",
        "name": "Test User",
        "email": "test@example.com",
        "access_token": "sekret",
        "token_type": "bearer",
    }
    output = pipeline(
        backend=backend,
        pipeline_index=0,
        strategy=strategy,
        response=response,
    )

    assert output["user"].username == "dummy-user"


def test_pipeline_with_new_user(slack_messages, strategy):
    backend = GithubOAuth2(strategy=strategy)
    response = {
        "id": "1234",
        "login": "dummy-user",
        "name": "Test User",
        "email": "test@example.com",
        "access_token": "sekret",
        "token_type": "bearer",
    }
    output = pipeline(
        backend=backend,
        pipeline_index=0,
        strategy=strategy,
        response=response,
    )

    user = output["user"]
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.username == "dummy-user"

    social = output["social"]
    assert social.user == user
    assert "sekret" not in social.extra_data.values()

    url = f"http://localhost:8000{user.get_staff_url()}"

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "job-server-registrations"
    assert text == f"New user ({user.username}) registered: <{url}>"


def test_pipeline_without_name(rf, slack_messages):
    request = rf.get("/")
    request.session = SessionStore()
    strategy = DjangoStrategy(request=request, storage=DjangoStorage())
    backend = GithubOAuth2(strategy=strategy)

    github_response = {
        "id": "1234",
        "login": "dummy-user",
        "name": "",
        "email": "test@example.com",
        "access_token": "sekret",
        "token_type": "bearer",
    }

    response = pipeline(
        backend=backend,
        pipeline_index=0,
        strategy=strategy,
        response=github_response,
    )

    # does the pipeline redirect when the response is missing a name?
    assert response.status_code == 302
    assert response.url.startswith(reverse("require-name"))

    # create a new request with our form submission
    request = rf.post("/", data={"name": "Test User"})
    request.session = SessionStore()
    strategy = DjangoStrategy(request=request, storage=DjangoStorage())
    backend = GithubOAuth2(strategy=strategy)

    output = pipeline(
        backend=backend,
        pipeline_index=0,
        strategy=strategy,
        response=github_response,
    )

    assert output["user"].name == "Test User"
