import responses
from django.conf import settings

from jobserver.management.commands.check_controller_status import Command as cd


def test_check_controller_status():
    with responses.RequestsMock() as rsps:
        # default rap api url
        url = settings.RAP_API_ENDPOINT

        rsps.add(responses.GET, url, body=b'{"method": "GET"}', status=200)

        result = cd.check_controller_status(url)
        assert result == b'{"method": "GET"}'
