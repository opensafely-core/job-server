"""Tests of SiteAlert-related staff views."""

from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from jobserver.models import SiteAlert
from staff.views.site_alerts import (
    SiteAlertCreate,
    SiteAlertDelete,
    SiteAlertList,
    SiteAlertUpdate,
)
from tests.factories import SiteAlertFactory


class TestSiteAlertViewsAuthorized:
    """Tests of SiteAlert-related staff views when authorized."""

    def test_list_view(self, rf, staff_area_administrator, site_alert):
        """Test that the list view displays a single site alert."""
        request = rf.get("/")
        request.user = staff_area_administrator
        response = SiteAlertList.as_view()(request)

        assert response.status_code == 200
        assert len(response.context_data["alerts"]) == 1

    def test_list_view_multiple(self, rf, staff_area_administrator):
        """Test that the list view displays multiple site alerts."""
        for _ in range(3):
            SiteAlertFactory()

        request = rf.get("/")
        request.user = staff_area_administrator
        response = SiteAlertList.as_view()(request)

        assert response.status_code == 200
        assert len(response.context_data["alerts"]) == 3

    def test_create_view_get(self, rf, staff_area_administrator):
        """Test that the create view GET displays an unpopulated form."""
        request = rf.get("/")
        request.user = staff_area_administrator
        response = SiteAlertCreate.as_view()(request)

        assert response.status_code == 200
        assert "form" in response.context_data
        assert not response.context_data["form"].is_bound
        assert response.context_data["form"].initial == {}

    def test_create_view_post(self, rf, staff_area_administrator):
        """Test that the create view POST creates a new site alert."""
        new_alert_data = {
            "title": "New Alert",
            "message": "This is a new alert message",
            "level": "info",
        }
        request = rf.post("/", new_alert_data, follow=True)
        request.user = staff_area_administrator
        with patch("django.contrib.messages.api.add_message"):
            response = SiteAlertCreate.as_view()(request)

        # SiteAlert created.
        new_alert = SiteAlert.objects.get(title="New Alert")
        assert new_alert.title == "New Alert"
        assert new_alert.message == "This is a new alert message"
        assert new_alert.level == "info"
        assert new_alert.created_by == staff_area_administrator
        assert new_alert.updated_by == staff_area_administrator

        # Re-directed to the edit URL for the new alert.
        assert response.status_code == 302
        assert response.url == reverse(
            "staff:site-alerts:edit", kwargs={"pk": new_alert.pk}
        )

    def test_update_view_get(self, rf, staff_area_administrator, site_alert):
        """Test GET request to the update view displays a populated form."""
        request = rf.get(f"/{site_alert.pk}")
        request.user = staff_area_administrator
        response = SiteAlertUpdate.as_view()(request, pk=site_alert.pk)

        assert response.status_code == 200
        assert "form" in response.context_data

        assert not response.context_data["form"].is_bound
        assert response.context_data["form"].instance == site_alert
        assert response.context_data["form"].initial["title"] == site_alert.title
        assert response.context_data["form"].initial["message"] == site_alert.message
        assert response.context_data["form"].initial["level"] == site_alert.level

    def test_update_view_post(self, rf, staff_area_administrator, site_alert):
        """Test that the update view POST updates the site alert."""
        new_alert_data = {
            "title": "New Alert",
            "message": "This is a new alert message",
            "level": "success",
        }
        request = rf.post("/{site_alert.pk}", new_alert_data, follow=True)
        request.user = staff_area_administrator
        with patch("django.contrib.messages.api.add_message"):
            response = SiteAlertUpdate.as_view()(request, pk=site_alert.pk)

        # SiteAlert updated.
        new_alert = SiteAlert.objects.get(title="New Alert")
        assert new_alert.title == "New Alert"
        assert new_alert.message == "This is a new alert message"
        assert new_alert.level == "success"
        assert new_alert.updated_by == staff_area_administrator
        # created_by not changed.
        assert new_alert.created_by == site_alert.created_by
        # Check we didn't somehow pick the same attributes as the factory did
        # and get the above right by accident.
        assert new_alert.title != site_alert.title
        assert new_alert.message != site_alert.message

        # Re-directed to the edit URL for the new alert.
        assert response.status_code == 302
        assert response.url == reverse(
            "staff:site-alerts:edit", kwargs={"pk": new_alert.pk}
        )

    def test_delete_view_get(self, rf, staff_area_administrator, site_alert):
        """Test GET request to the delete view doesn't delete the alert."""
        request = rf.get(f"/{site_alert.pk}")
        request.user = staff_area_administrator
        with patch("django.contrib.messages.api.add_message"):
            response = SiteAlertDelete.as_view()(request, pk=site_alert.pk)

        assert response.status_code == 200
        assert SiteAlert.objects.filter(pk=site_alert.pk).exists()

    def test_delete_view_post(self, rf, staff_area_administrator, site_alert):
        """Test that the delete view deletes an existing alert."""
        request = rf.post(f"/{site_alert.pk}")
        request.user = staff_area_administrator
        with patch("django.contrib.messages.api.add_message"):
            response = SiteAlertDelete.as_view()(request, pk=site_alert.pk)

        assert response.status_code == 302
        assert response.url == reverse("staff:site-alerts:list")
        assert not SiteAlert.objects.filter(pk=site_alert.pk).exists()


class TestSiteAlertViewsUnauthorized:
    """Tests of SiteAlert-related staff views when unauthorized.

    Nothing is permitted."""

    def test_list_view(self, rf, site_alert):
        """Test that the list view requires authorization."""
        request = rf.get("/")
        request.user = AnonymousUser()
        with pytest.raises(PermissionDenied):
            SiteAlertList.as_view()(request)

    def test_create_view_get(self, rf):
        """Test that the create view GET requires authorization."""
        request = rf.get("/")
        request.user = AnonymousUser()
        with pytest.raises(PermissionDenied):
            SiteAlertCreate.as_view()(request)

    def test_create_view_post(self, rf):
        """Test that the create view POST requires authorization."""
        new_alert_data = {
            "title": "New Alert",
            "message": "This is a new alert message",
            "level": "info",
        }
        request = rf.post("/", new_alert_data, follow=True)
        request.user = AnonymousUser()
        with pytest.raises(PermissionDenied):
            SiteAlertCreate.as_view()(request)

    def test_update_view_get(self, rf, site_alert):
        """Test GET request to the update view requires authorization."""
        request = rf.get(f"/{site_alert.pk}")
        request.user = AnonymousUser()
        with pytest.raises(PermissionDenied):
            SiteAlertUpdate.as_view()(request, pk=site_alert.pk)

    def test_update_view_post(self, rf, site_alert):
        """Test that the update view POST requires authorization."""
        new_alert_data = {
            "title": "New Alert",
            "message": "This is a new alert message",
            "level": "success",
        }
        request = rf.post("/{site_alert.pk}", new_alert_data, follow=True)
        request.user = AnonymousUser()
        with pytest.raises(PermissionDenied):
            SiteAlertUpdate.as_view()(request, pk=site_alert.pk)

    def test_delete_view_get(self, rf, site_alert):
        """Test GET request to the delete view doesn't delete the alert."""
        request = rf.get(f"/{site_alert.pk}")
        request.user = AnonymousUser()
        with pytest.raises(PermissionDenied):
            SiteAlertDelete.as_view()(request, pk=site_alert.pk)

    def test_delete_view_post(self, rf, site_alert):
        """Test that the delete view requires authorization."""
        request = rf.post(f"/{site_alert.pk}")
        request.user = AnonymousUser()
        with pytest.raises(PermissionDenied):
            SiteAlertDelete.as_view()(request, pk=site_alert.pk)
