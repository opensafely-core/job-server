import pytest
from django.urls import reverse

from ..factories import BackendFactory, JobFactory, JobRequestFactory, UserFactory


class TestDbMaintenanceModeContextProcessor:
    """Tests of the db_maintenance_mode context processor."""

    def setup_method(self):
        self.user = UserFactory()
        self.job_request = JobRequestFactory(created_by=self.user)
        self.job = JobFactory(job_request=self.job_request)

    @pytest.mark.parametrize(
        "is_user_authenticated, is_backend_in_maintenance, is_banner_expected",
        [
            (True, True, True),  # authenticated user + maintenance -> banner shown
            (True, False, False),  # authenticated user + no maintenance -> no banner
            (False, True, False),  # anonymous user + maintenance -> no banner
            (False, False, False),  # anonymous user + no maintenance -> no banner
        ],
        ids=[
            "authenticated+maintenance",
            "authenticated+no-maintenance",
            "anonymous+maintenance",
            "anonymous+no-maintenance",
        ],
    )
    @pytest.mark.usefixtures("clear_cache", "enable_db_maintenance_context_processor")
    def test_db_maintenance_banner_visibility(
        self,
        client,
        is_user_authenticated,
        is_backend_in_maintenance,
        is_banner_expected,
    ):
        BackendFactory(slug="emis", is_in_maintenance_mode=False)
        if is_backend_in_maintenance:
            BackendFactory(slug="tpp", is_in_maintenance_mode=True)
        else:
            BackendFactory(slug="tpp", is_in_maintenance_mode=False)

        request_url = reverse(
            "job-detail",
            kwargs={
                "project_slug": self.job.job_request.workspace.project.slug,
                "workspace_slug": self.job.job_request.workspace.name,
                "pk": self.job.job_request.pk,
                "identifier": self.job.identifier,
            },
        )

        if is_user_authenticated:
            client.force_login(self.user)

        response = client.get(request_url)
        assert response.status_code == 200

        is_banner_present = b"db-maintenance-banner" in response.content
        assert is_banner_present == is_banner_expected
