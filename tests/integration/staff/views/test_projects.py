import pytest
from django.urls import reverse

from jobserver.authorization.roles import ServiceAdministrator, StaffAreaAdministrator
from jobserver.models import AuditableEvent, Project
from jobserver.utils import set_from_qs
from tests.factories import OrgFactory, ProjectFactory, UserFactory


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


class TestProjectCreation:
    """Tests of the project creation user flow."""

    def test_projectcreate_authorized(self, client):
        """
        Test that a user with permission can access the ProjectCreate view.
        """
        user = UserFactory(roles=[ServiceAdministrator])

        client.force_login(user)

        response = client.get(reverse("staff:project-create"))

        assert response.status_code == 200
        assert not response.context_data["form"].is_bound

    def test_projectcreated_authorized(self, client):
        """
        Test that a user with permission can access the ProjectCreated view.
        """
        user = UserFactory(roles=[ServiceAdministrator])
        project = ProjectFactory()

        client.force_login(user)

        response = client.get(
            reverse("staff:project-created", kwargs={"slug": project.slug})
        )

        assert response.status_code == 200

    @pytest.mark.django_db(transaction=True)
    def test_projectcreate_post_success(self, client, slack_messages):
        """
        Test a successful POST to the ProjectCreate view.

        * A user with permission can access the ProjectCreate view.
        * When valid data is submitted then:
            * The user is redirected to the ProjectCreated page
            * A new project is saved to the db with:
                * created_by and updated_by = current user.
                * copilot, orgs, name, and number fields have the values from the form data.
                * created_by, updated_by and status are populated by Project model default values
            * An AuditableEvent is created for the new project instance.
            * A Slack message is sent to the copilot support channel.
        """
        user = UserFactory(roles=[ServiceAdministrator])
        copilot = UserFactory()
        org = OrgFactory()

        data = {
            "name": "test1",
            "number": "1234567832",
            "orgs": [str(org.pk)],
            "copilot": str(copilot.pk),
        }

        client.force_login(user)

        response = client.post(reverse("staff:project-create"), data, follow=True)

        new_project = Project.objects.first()
        url = reverse("staff:project-created", kwargs={"slug": new_project.slug})

        assert response.status_code == 200
        assert response.redirect_chain == [(url, 302)]

        assert new_project.copilot == copilot
        assert new_project.created_by == user
        assert new_project.name == data["name"]
        assert new_project.number == data["number"]
        assert set_from_qs(new_project.orgs.all()) == {org.pk}
        assert new_project.updated_by == user

        assert AuditableEvent.objects.filter(target_id=new_project.pk).count() == 1

        assert len(slack_messages) == 1
        message, channel = slack_messages[0]
        assert channel == "co-pilot-support"
