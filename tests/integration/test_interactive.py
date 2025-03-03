from unittest.mock import patch

from jobserver.views.reports import PublishRequestCreate

from ..fakes import FakeGitHubAPI


def assert_publish_page_is_locked(analysis, client):
    with patch.object(PublishRequestCreate, "get_github_api", FakeGitHubAPI):
        response = client.post(analysis.get_publish_url())
        assert response.status_code == 200
        assert (
            response.template_name == "interactive/publish_request_create_locked.html"
        )
