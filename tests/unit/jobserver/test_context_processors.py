from django.urls import reverse

from jobserver.context_processors import can_view_staff_area, nav

from ...factories import UserFactory


def test_can_view_staff_area_with_core_developer(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    assert can_view_staff_area(request)["user_can_view_staff_area"]


def test_can_view_staff_area_without_core_developer(rf):
    request = rf.get("/")
    request.user = UserFactory()

    assert not can_view_staff_area(request)["user_can_view_staff_area"]


def test_can_view_staff_area_makes_no_db_queries(
    rf, core_developer, django_assert_num_queries
):
    request = rf.get("/")
    request.user = core_developer

    with django_assert_num_queries(0):
        assert can_view_staff_area(request)["user_can_view_staff_area"]


def test_nav_jobs(rf):
    request = rf.get(reverse("job-list"))
    request.user = UserFactory()

    jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is True
    assert status["is_active"] is False


def test_nav_status(rf):
    request = rf.get(reverse("status"))
    request.user = UserFactory()

    jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is False
    assert status["is_active"] is True


def test_nav_makes_no_db_queries(rf, django_assert_num_queries):
    request = rf.get(reverse("status"))
    request.user = UserFactory()

    with django_assert_num_queries(0):
        assert nav(request)
