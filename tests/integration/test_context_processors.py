import pytest
from django.urls import reverse

from ..factories import BackendFactory, JobFactory, JobRequestFactory, UserFactory


class TestDbMaintenanceModeContextProcessor:
    """Tests of the db_maintenance_mode context processor."""

    def setup_method(self):
        self.user = UserFactory()
        self.job_request = JobRequestFactory(created_by=self.user)
        self.job = JobFactory(job_request=self.job_request)

    @pytest.mark.usefixtures("clear_cache", "enable_db_maintenance_context_processor")
    def test_banner_in_rendered_template_for_db_in_maintenance(self, client):
        BackendFactory(slug="tpp", jobrunner_state={"mode": {"v": "db-maintenance"}})
        BackendFactory(slug="emis", jobrunner_state={"paused": {"v": ""}})

        request_url = reverse(
            "job-detail",
            kwargs={
                "project_slug": self.job.job_request.workspace.project.slug,
                "workspace_slug": self.job.job_request.workspace.name,
                "pk": self.job.job_request.pk,
                "identifier": self.job.identifier,
            },
        )

        response = client.get(request_url)

        assert response.status_code == 200
        assert b"db-maintenance-banner" in response.content

    @pytest.mark.usefixtures("clear_cache", "enable_db_maintenance_context_processor")
    def test_banner_not_in_rendered_template_for_db_not_in_maintenance(self, client):
        BackendFactory(slug="tpp", jobrunner_state={"mode": {"v": ""}})
        BackendFactory(slug="emis", jobrunner_state={"paused": {"v": ""}})

        request_url = reverse(
            "job-detail",
            kwargs={
                "project_slug": self.job.job_request.workspace.project.slug,
                "workspace_slug": self.job.job_request.workspace.name,
                "pk": self.job.job_request.pk,
                "identifier": self.job.identifier,
            },
        )

        response = client.get(request_url)

        assert response.status_code == 200
        assert b"db-maintenance-banner" not in response.content
