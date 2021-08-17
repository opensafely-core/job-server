import pytest

from staff.views.index import Index

from ....factories import BackendFactory, UserFactory


@pytest.mark.django_db
def test_index_without_search(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    response = Index.as_view()(request)

    assert response.context_data["q"] is None
    assert response.context_data["results"] == []


@pytest.mark.django_db
def test_index_search(rf, core_developer):
    backend = BackendFactory(name="GHickman's Research Thing")
    BackendFactory.create_batch(2)

    user = UserFactory(username="ghickman")
    UserFactory.create_batch(5)

    request = rf.get("/?q=ghickman")
    request.user = core_developer

    response = Index.as_view()(request)

    assert response.context_data["q"] == "ghickman"

    results = response.context_data["results"]

    assert len(results) == 2
    assert results == [
        ("Backend", [backend]),
        ("User", [user]),
    ]
