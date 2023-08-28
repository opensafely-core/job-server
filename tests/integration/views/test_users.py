def test_userlist(client):
    response = client.get("/users/")

    assert response.status_code == 200
