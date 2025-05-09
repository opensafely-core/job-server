import socket
import urllib

import pytest
import requests
from pytest_socket import SocketBlockedError


@pytest.mark.django_db(False)
class TestNetworkBlocked:
    """Test that network/socket access is blocked during tests."""

    def test_network_blocked_socket(self):
        """Test that network/socket access is blocked via `socket`."""
        with pytest.raises(SocketBlockedError):
            socket.socket()

    def test_network_blocked_requests(self):
        """Test that network/socket access is blocked via `requests`."""
        with pytest.raises(SocketBlockedError):
            requests.get("https://example.com")

    def test_network_blocked_urllib(self):
        """Test that network/socket access is blocked via `urllib`."""
        with pytest.raises(SocketBlockedError):
            urllib.request.urlopen("https://example.com")
