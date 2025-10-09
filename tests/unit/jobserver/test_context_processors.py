from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import resolve, reverse

from jobserver.context_processors import (
    can_view_staff_area,
    db_maintenance_mode,
    in_production,
    nav,
    site_alerts,
)

from ...factories import BackendFactory, JobFactory, JobRequestFactory, UserFactory


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


class TestCanViewStaffArea:
    """Tests of the can_view_staff_area context processor."""

    def test_with_staff_area_administrator(self, rf, staff_area_administrator):
        """Test that Staff Area Admins get access."""
        request = rf.get("/")
        request.user = staff_area_administrator

        assert can_view_staff_area(request)["user_can_view_staff_area"]

    def test_without_staff_area_administrator(self, rf):
        """Test that non-Staff Area Admins do not get access."""
        request = rf.get("/")
        request.user = UserFactory()

        assert not can_view_staff_area(request)["user_can_view_staff_area"]

    def test_with_no_user(self, rf):
        """Test that requests without users don't have access."""
        request = rf.get("/")

        assert not can_view_staff_area(request)["user_can_view_staff_area"]

    def test_makes_no_db_queries(
        self, rf, staff_area_administrator, django_assert_num_queries
    ):
        """Test that the function does not hit the database."""
        request = rf.get("/")
        request.user = staff_area_administrator

        with django_assert_num_queries(0):
            assert can_view_staff_area(request)["user_can_view_staff_area"]


class TestNav:
    """Tests of the nav context processor."""

    def test_jobs(self, rf):
        request = rf.get(reverse("job-list"))
        request.user = UserFactory()

        jobs, status = nav(request)["nav"]

        assert jobs["is_active"] is True
        assert status["is_active"] is False

    def test_status(self, rf):
        request = rf.get(reverse("status"))
        request.user = UserFactory()

        jobs, status = nav(request)["nav"]

        assert jobs["is_active"] is False
        assert status["is_active"] is True

    def test_makes_no_db_queries(self, rf, django_assert_num_queries):
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

    def test_no_user(self, rf, site_alert):
        """Test that requests without users don't get site_alerts in the context."""
        request = rf.get("/")

        context = site_alerts(request)
        assert "site_alerts" in context
        assert context["site_alerts"] is None


class TestDbMaintenanceModeContextProcessor:
    """Tests of the db_maintenance_mode context processor."""

    def setup_method(self):
        self.tpp = BackendFactory(slug="tpp", is_in_maintenance_mode=True)
        self.emis = BackendFactory(slug="emis", is_in_maintenance_mode=False)
        self.other = BackendFactory(slug="other", is_in_maintenance_mode=True)

    @pytest.mark.usefixtures("clear_cache", "enable_db_maintenance_context_processor")
    def test_expected_attribute_values_for_banner_display_url(self, rf):
        """Adds expected db maintenance status values for allowed backends on pre-specified banner display URLs."""

        user = UserFactory()
        job_request = JobRequestFactory(created_by=user)
        job = JobFactory(job_request=job_request)

        request_url = reverse(
            "job-detail",
            kwargs={
                "project_slug": job.job_request.workspace.project.slug,
                "workspace_slug": job.job_request.workspace.name,
                "pk": job.job_request.pk,
                "identifier": job.identifier,
            },
        )

        request = rf.get(request_url)
        request.resolver_match = resolve(request.path_info)

        with (
            patch(
                "jobserver.context_processors.BANNER_DISPLAY_URL_NAMES", ["job-detail"]
            ),
            patch(
                "jobserver.context_processors.Backend.objects.get_db_maintenance_mode_statuses",
                return_value={"tpp": True, "emis": False},
            ),
        ):
            context = db_maintenance_mode(request)

        assert context["tpp_maintenance_banner"] is True
        assert context["emis_maintenance_banner"] is False

    @pytest.mark.usefixtures("enable_db_maintenance_context_processor")
    def test_attributes_not_added_for_non_banner_display_url(self, rf):
        """Returns empty dict for non-banner-display URLs."""

        request = rf.get(reverse("job-list"))
        request.resolver_match = resolve(request.path_info)

        with (
            patch(
                "jobserver.context_processors.BANNER_DISPLAY_URL_NAMES", ["job-detail"]
            ),
        ):
            context = db_maintenance_mode(request)

        assert context == {}

    @pytest.mark.usefixtures("enable_db_maintenance_context_processor")
    def test_attributes_not_added_for_no_resolver_match_url(self, rf):
        """Returns empty dict if request has no resolver_match attribute."""
        request = rf.get("/no-match-url/")
        context = db_maintenance_mode(request)
        assert context == {}
