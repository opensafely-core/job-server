from tests.factories import UserFactory


def test_userdetail(client):
    user = UserFactory()

    response = client.get(user.get_absolute_url())

    assert response.status_code == 200


def test_usereventlog(client):
    user = UserFactory()

    response = client.get(user.get_logs_url())

    assert response.status_code == 200


def test_userlist(client):
    response = client.get("/users/")

    assert response.status_code == 200
