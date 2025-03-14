from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from jobserver.context_processors import (
    can_view_staff_area,
    in_production,
    nav,
    site_alerts,
)

from ...factories import UserFactory


class TestInProduction:
    """Tests of the in_production context processor."""

    def test_in_production_mode(self, rf, settings):
        """Test when the site is in production mode (DEBUG=False)."""
        settings.DEBUG = False
        request = rf.get("/")
        assert in_production(request)["in_production"] is True

    def test_in_debug_mode(self, rf, settings):
        """Test when the site is in debug mode (DEBUG=True)."""
        settings.DEBUG = True
        request = rf.get("/")
        assert in_production(request)["in_production"] is False


def test_can_view_staff_area_with_staff_area_administrator(
    rf, staff_area_administrator
):
    request = rf.get("/")
    request.user = staff_area_administrator

    assert can_view_staff_area(request)["user_can_view_staff_area"]


def test_can_view_staff_area_without_staff_area_administrator(rf):
    request = rf.get("/")
    request.user = UserFactory()

    assert not can_view_staff_area(request)["user_can_view_staff_area"]


def test_can_view_staff_area_makes_no_db_queries(
    rf, staff_area_administrator, django_assert_num_queries
):
    request = rf.get("/")
    request.user = staff_area_administrator

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


class TestSiteAlertContextProcessor:
    """Tests of the site_alerts context processor."""

    def test_authenticated(self, rf, staff_area_administrator, site_alert):
        """Test that authenticated users get site_alerts in the context."""
        request = rf.get("/")
        request.user = staff_area_administrator
        context = site_alerts(request)
        assert "site_alerts" in context
        assert len(context["site_alerts"]) == 1
        assert context["site_alerts"].first() == site_alert

    def test_unauthenticated(self, rf, staff_area_administrator, site_alert):
        """Test that unauthenticated users don't get site_alerts in the context."""
        request = rf.get("/")
        request.user = AnonymousUser()

        context = site_alerts(request)
        assert "site_alerts" in context
        assert context["site_alerts"] is None
