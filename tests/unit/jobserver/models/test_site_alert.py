from django.urls import reverse

from jobserver.models import SiteAlert
from tests.factories import SiteAlertFactory


class TestSiteAlertModel:
    def test_str_representation_with_title(self):
        """Test the string representation of an alert with a title."""
        site_alert = SiteAlertFactory(
            level=SiteAlert.Level.WARNING,
            title="Test Alert",
            message="This will not be included",
        )
        assert str(site_alert) == "Warning: Test Alert"

    def test_str_representation_without_title(self, user):
        """Test the string representation of an alert without a title."""
        site_alert_no_title = SiteAlert.objects.create(
            message="This is a test alert with no title",
            title="",
            level=SiteAlert.Level.INFO,
        )
        assert str(site_alert_no_title) == "Info: This is a test alert with no title"

    def test_repr_representation(self):
        """Test the internal representation of an alert."""
        site_alert = SiteAlertFactory(
            level=SiteAlert.Level.DANGER, title="Test Alert", message="Test Message"
        )
        assert repr(site_alert) == (
            "<SiteAlert title: 'Test Alert' message: 'Test Message' level: danger>"
        )

    def test_ordering(self, site_alert):
        """Test that alerts are ordered by created_at (newest first)."""
        newer_alert = SiteAlertFactory()

        alerts = list(SiteAlert.objects.all())
        assert len(alerts) == 2
        assert alerts[0] == newer_alert
        assert alerts[1] == site_alert

    def test_edit_url(self, site_alert):
        """Test the edit_url property returns the correct URL."""
        expected_url = reverse("staff:site-alerts:edit", kwargs={"pk": site_alert.pk})
        assert site_alert.edit_url == expected_url

    def test_delete_url(self, site_alert):
        """Test the delete_url property returns the correct URL."""
        expected_url = reverse("staff:site-alerts:delete", kwargs={"pk": site_alert.pk})
        assert site_alert.delete_url == expected_url
