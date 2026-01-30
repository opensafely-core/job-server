from jobserver.authorization.roles import ServiceAdministrator, StaffAreaAdministrator
from tests.factories import UserFactory


class TestProjectListCreateProjectButton:
    """Tests of the Create a Project button on the Staff Area Projects page."""

    def test_create_project_button_in_rendered_template_for_authorised_user(
        self, client
    ):
        user = UserFactory(roles=[StaffAreaAdministrator, ServiceAdministrator])

        client.force_login(user)

        response = client.get("/staff/projects/")

        assert response.status_code == 200
        assert "Create a project" in response.text

    def test_create_project_button_not_in_rendered_template_for_unauthorised_user(
        self, client, staff_area_administrator
    ):
        user = staff_area_administrator

        client.force_login(user)

        response = client.get("/staff/projects/")

        assert response.status_code == 200
        assert "Create a project" not in response.text
