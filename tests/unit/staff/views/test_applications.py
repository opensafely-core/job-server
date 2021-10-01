import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from jobserver.utils import set_from_qs
from staff.views.applications import ApplicationDetail, ApplicationList

from ....factories import ApplicationFactory, UserFactory


def test_applicationdetail_success(rf, core_developer):
    application = ApplicationFactory()

    request = rf.get("/")
    request.user = core_developer

    response = ApplicationDetail.as_view()(request, pk=application.pk)

    assert response.status_code == 200

    assert response.context_data["application"] == application


def test_applicationdetail_with_unknown_user(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ApplicationDetail.as_view()(request, pk=0)


def test_applicationdetail_without_core_dev_role(rf):
    application = ApplicationFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ApplicationDetail.as_view()(request, pk=application.pk)


def test_applicationlist_search(rf, core_developer):
    app1 = ApplicationFactory(created_by=UserFactory(first_name="ben"))
    app2 = ApplicationFactory(created_by=UserFactory(username="ben"))
    ApplicationFactory(created_by=UserFactory(username="seb"))

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = ApplicationList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 2
    assert set_from_qs(response.context_data["object_list"]) == {app1.pk, app2.pk}


def test_applicationlist_success(rf, core_developer):
    ApplicationFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = ApplicationList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 5
