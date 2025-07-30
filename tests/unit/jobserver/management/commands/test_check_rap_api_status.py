import responses
import responses.matchers
from django.conf import settings

from jobserver.management.commands.check_rap_api_status import Command as cd


def test_check_rap_api_status():
    with responses.RequestsMock() as rsps:
        # default rap api url
        url = settings.RAP_API_ENDPOINT
        api_token = settings.RAP_API_TOKEN

        rsps.add(
            responses.GET,
            f"{url}/backend/status",
            body=b'{"method": "GET"}',
            match=[responses.matchers.header_matcher({"Authorization": api_token})],
            status=200,
        )

        result = cd.check_rap_api_status(url, api_token)
        assert result == b'{"method": "GET"}'
