import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import BadRequest
from django.http import Http404

from jobserver.authorization import OutputPublisher, TechnicalReviewer
from jobserver.models import Backend
from jobserver.views.users import Settings, UserDetail, UserList

from ...factories import (
    BackendMembershipFactory,
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_settings_get(rf):
    UserFactory()
    user2 = UserFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = user2
    response = Settings.as_view()(request)

    assert response.status_code == 200

    # check the view was constructed with the request user
    assert response.context_data["object"] == user2


@pytest.mark.django_db
def test_settings_post(rf):
    UserFactory()
    user2 = UserFactory(notifications_email="original@example.com")

    data = {"notifications_email": "changed@example.com"}
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user2

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = Settings.as_view()(request)
    assert response.status_code == 302
    assert response.url == "/"

    user2.refresh_from_db()

    assert user2.notifications_email == "changed@example.com"

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Settings saved successfully"


@pytest.mark.django_db
def test_userdetail_get_success(rf, core_developer):
    org = OrgFactory()
    project1 = ProjectFactory(org=org)
    project2 = ProjectFactory(org=org)
    user = UserFactory(roles=[OutputPublisher, TechnicalReviewer])

    # link the user to some Backends
    user.backend_memberships.create(backend=Backend.objects.get(name="test"))
    user.backend_memberships.create(backend=Backend.objects.get(name="tpp"))

    # link the user to the Org
    OrgMembershipFactory(org=org, user=user)

    # link the user to the Projects
    ProjectMembershipFactory(project=project1, user=user)
    ProjectMembershipFactory(project=project2, user=user)

    request = rf.get("/")
    request.user = core_developer

    response = UserDetail.as_view()(request, username=user.username)

    assert response.status_code == 200

    assert set(response.context_data["orgs"]) == {org}
    assert set(response.context_data["projects"]) == {project1, project2}
    assert response.context_data["user"] == user


@pytest.mark.django_db
def test_userdetail_post_success(rf, core_developer):
    org = OrgFactory()
    project1 = ProjectFactory(org=org)
    project2 = ProjectFactory(org=org)
    user = UserFactory(roles=[OutputPublisher, TechnicalReviewer])

    # link the user to some Backends
    user.backend_memberships.create(backend=Backend.objects.get(name="test"))
    user.backend_memberships.create(backend=Backend.objects.get(name="tpp"))

    # link the user to the Org
    OrgMembershipFactory(org=org, user=user)

    # link the user to the Projects
    ProjectMembershipFactory(project=project1, user=user)
    ProjectMembershipFactory(project=project2, user=user)

    data = {
        "backends": ["test"],
        "is_superuser": ["on"],
        "roles": ["jobserver.authorization.roles.OutputPublisher"],
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = UserDetail.as_view()(request, username=user.username)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == user.get_absolute_url()

    user.refresh_from_db()
    assert list(user.backends.values_list("name", flat=True)) == ["test"]
    assert user.roles == [OutputPublisher]
    assert user.is_superuser


@pytest.mark.django_db
def test_userdetail_post_with_unknown_backend(rf, core_developer):
    org = OrgFactory()
    project1 = ProjectFactory(org=org)
    project2 = ProjectFactory(org=org)
    user = UserFactory(roles=[OutputPublisher, TechnicalReviewer])

    # link the user to some Backends
    user.backend_memberships.create(backend=Backend.objects.get(name="test"))
    user.backend_memberships.create(backend=Backend.objects.get(name="tpp"))

    # link the user to the Org
    OrgMembershipFactory(org=org, user=user)

    # link the user to the Projects
    ProjectMembershipFactory(project=project1, user=user)
    ProjectMembershipFactory(project=project2, user=user)

    data = {
        "backends": ["not-a-real-backend"],
        "is_superuser": [""],
        "roles": ["jobserver.authorization.roles.OutputPublisher"],
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = UserDetail.as_view()(request, username=user.username)

    assert response.status_code == 200, response.url

    # check we get an error from the form, and thus are passing in the
    # submitted data correctly
    expected = {
        "backends": [
            "Select a valid choice. not-a-real-backend is not one of the available choices."
        ]
    }
    assert response.context_data["form"].errors == expected

    # check we're rendering the appropriate error in the template
    assert (
        "not-a-real-backend is not one of the available choices."
        in response.rendered_content
    )


@pytest.mark.django_db
def test_userdetail_post_with_unknown_role(rf, core_developer):
    org = OrgFactory()
    project1 = ProjectFactory(org=org)
    project2 = ProjectFactory(org=org)
    user = UserFactory(roles=[OutputPublisher, TechnicalReviewer])

    # link the user to some Backends
    user.backend_memberships.create(backend=Backend.objects.get(name="test"))
    user.backend_memberships.create(backend=Backend.objects.get(name="tpp"))

    # link the user to the Org
    OrgMembershipFactory(org=org, user=user)

    # link the user to the Projects
    ProjectMembershipFactory(project=project1, user=user)
    ProjectMembershipFactory(project=project2, user=user)

    data = {
        "backends": ["test", "tpp"],
        "is_superuser": ["on"],
        "roles": ["not-a-real-role"],
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = UserDetail.as_view()(request, username=user.username)

    assert response.status_code == 200, response.url

    # check we get an error from the form, and thus are passing in the
    # submitted data correctly
    expected = {
        "roles": [
            "Select a valid choice. not-a-real-role is not one of the available choices."
        ]
    }
    assert response.context_data["form"].errors == expected

    # check we're rendering the appropriate error in the template
    assert (
        "not-a-real-role is not one of the available choices."
        in response.rendered_content
    )


@pytest.mark.django_db
def test_userdetail_with_unknown_user(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        UserDetail.as_view()(request, username="test")


@pytest.mark.django_db
def test_userdetail_without_core_dev_role(rf):
    request = rf.get("/")
    request.user = UserFactory()

    response = UserDetail.as_view()(request, username="test")

    assert response.status_code == 403


@pytest.mark.django_db
def test_userlist_filter_by_backend(rf, core_developer):
    emis = Backend.objects.get(name="emis")
    tpp = Backend.objects.get(name="tpp")

    BackendMembershipFactory(user=UserFactory(), backend=emis)
    BackendMembershipFactory(user=UserFactory(), backend=tpp)

    request = rf.get(f"/?backend={emis.pk}")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_userlist_filter_by_invalid_backend(rf, core_developer):
    request = rf.get("/?backend=test")
    request.user = core_developer

    with pytest.raises(BadRequest):
        UserList.as_view()(request)


@pytest.mark.django_db
def test_userlist_filter_by_role(rf, core_developer):
    UserFactory(roles=[OutputPublisher])
    UserFactory(roles=[TechnicalReviewer])

    request = rf.get("/?role=OutputPublisher")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_userlist_filter_by_invalid_role(rf, core_developer):
    request = rf.get("/?backend=unknown")
    request.user = core_developer

    with pytest.raises(BadRequest):
        UserList.as_view()(request)


@pytest.mark.django_db
def test_userlist_find_by_username(rf, core_developer):
    UserFactory(username="ben")
    UserFactory(first_name="ben")
    UserFactory(username="seb")

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 2


@pytest.mark.django_db
def test_userlist_success(rf, core_developer):
    UserFactory.create_batch(5)

    request = rf.get(MEANINGLESS_URL)
    request.user = core_developer

    response = UserList.as_view()(request)

    assert response.status_code == 200

    # the core_developer fixture creates a User object as well as the 5 we
    # created in the batch call above
    assert len(response.context_data["object_list"]) == 6
