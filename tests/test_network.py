import socket
import urllib

import pytest
import requests
from pytest_socket import SocketConnectBlockedError


# pytest-socket adds warnings on socket use.
# In our tests, we raise errors for warnings.
# These warnings are expected here,
# so we should ignore for these tests only.
# If we have a network access warning elsewhere,
# it would be helpful to have the failure.
pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.mark.django_db(False)
class TestNetworkBlocked:
    """Test that network/socket access is blocked during tests."""

    def test_network_blocked_socket(self):
        """Test that non-localhost network/socket access is blocked via `socket`."""
        with pytest.raises(SocketConnectBlockedError):
            # We previously used socket.socket() to test this behaviour.
            # But we need to allow localhost sockets for database access,
            # as of pytest-socket v0.8.0.
            # So test connection to a non-localhost IP
            # that should not be connectable.
            # 192.0.2.176 is an IP in the TEST-NET-1 range:
            # https://datatracker.ietf.org/doc/html/rfc5737
            socket.create_connection(("192.0.2.176", 443), timeout=0.001)

    def test_network_blocked_requests(self):
        """Test that network/socket access is blocked via `requests`."""
        with pytest.raises(SocketConnectBlockedError):
            requests.get("https://example.com")

    def test_network_blocked_urllib(self):
        """Test that network/socket access is blocked via `urllib`."""
        with pytest.raises(SocketConnectBlockedError):
            urllib.request.urlopen("https://example.com")
