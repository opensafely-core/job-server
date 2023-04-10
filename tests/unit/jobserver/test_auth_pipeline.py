from jobserver.auth_pipeline import pipeline

from ...factories import UserFactory, UserSocialAuthFactory


def test_pipeline_with_existing_user():
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
    output = pipeline(response)

    assert output["user"].username == "dummy-user"


def test_pipeline_with_new_user(slack_messages):
    response = {
        "id": "1234",
        "login": "dummy-user",
        "name": "Test User",
        "email": "test@example.com",
        "access_token": "sekret",
        "token_type": "bearer",
    }
    output = pipeline(response)

    user = output["user"]
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.notifications_email == "test@example.com"
    assert user.username == "dummy-user"

    social = output["social"]
    assert social.user == user
    assert social.extra_data["access_token"] == "sekret"

    url = f"http://localhost:8000{user.get_staff_url()}"

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "job-server-registrations"
    assert text == f"New user ({user.username}) registered: <{url}>"
