import pytest
from django.urls import reverse

from jobserver.authorization.roles import (
    ServiceAdministrator,
    StaffAreaAdministrator,
    TechSupport,
)
from jobserver.models import AuditableEvent, Project
from jobserver.utils import set_from_qs
from tests.factories import (
    CreateProjectFormDataFactory,
    OrgFactory,
    ProjectFactory,
    UserFactory,
)


class TestProjectListCreateProjectButton:
    """Tests of the Create a Project button on the Staff Area Projects page."""

    @pytest.mark.parametrize(
        "additional_role",
        [ServiceAdministrator, TechSupport],
    )
    def test_create_project_button_in_rendered_template_for_authorised_user(
        self, client, additional_role
    ):
        user = UserFactory(roles=[StaffAreaAdministrator, additional_role])

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

    def test_projectcreate_unauthorised(self, client, staff_area_administrator):
        user = staff_area_administrator

        client.force_login(user)

        response = client.post(reverse("staff:project-create"))
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "role",
        [ServiceAdministrator, TechSupport],
    )
    def test_projectcreate_selects_org_from_url_when_multiple_orgs_exist(
        self, client, role
    ):
        user = UserFactory(roles=[role])
        bennett_org = OrgFactory(slug="bennett-institute")
        OrgFactory(slug="university-of-oxford")
        OrgFactory(slug="phc-university-of-oxford")

        client.force_login(user)

        response = client.get(
            f"{reverse('staff:project-create')}?org-slug={bennett_org.slug}"
        )

        assert response.status_code == 200
        selected_orgs = response.context_data["form"]["orgs"].value()
        assert selected_orgs == bennett_org.pk

    @pytest.mark.parametrize(
        "role_fixture_name",
        ["service_administrator", "tech_support"],
    )
    @pytest.mark.django_db(transaction=True)
    def test_projectcreate_post_success(
        self, client, request, slack_messages, role_fixture_name
    ):
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
        role_fixture = request.getfixturevalue(role_fixture_name)
        user = role_fixture
        data = CreateProjectFormDataFactory()

        client.force_login(user)

        response = client.post(reverse("staff:project-create"), data, follow=True)

        new_project = Project.objects.first()
        url = reverse("staff:project-created", kwargs={"slug": new_project.slug})

        assert response.status_code == 200
        assert response.redirect_chain == [(url, 302)]

        assert new_project.copilot.pk == int(data["copilot"])
        assert new_project.created_by == user
        assert new_project.name == data["name"]
        assert new_project.number == data["number"]
        assert set_from_qs(new_project.orgs.all()) == {int(data["orgs"])}
        assert new_project.updated_by == user

        assert AuditableEvent.objects.filter(target_id=new_project.pk).count() == 1

        assert len(slack_messages) == 1
        message, channel = slack_messages[0]
        assert channel == "co-pilot-support"

    @pytest.mark.parametrize(
        "role_fixture_name",
        ["service_administrator", "tech_support"],
    )
    # parametrisation covers both empty and omitted values for each
    # required field when POSTing to the ProjectCreateForm.
    @pytest.mark.parametrize("field", ["name", "orgs", "copilot"])
    @pytest.mark.parametrize("missing_data", ["empty", "omitted"])
    def test_projectcreate_post_with_missing_data(
        self, client, request, slack_messages, role_fixture_name, field, missing_data
    ):
        """
        Test an unsuccessful POST to the ProjectCreate view with missing data.

        * When the form is submitted with missing data:
            * ProjectCreate view successfully re-renders
            * The bound form and error are in the response context
            * A new project is not created in the db
            * A new AuditableEvent is not created
            * A Slack message is not sent to the copilot support channel.
        """
        role_fixture = request.getfixturevalue(role_fixture_name)
        user = role_fixture
        projects_count = Project.objects.count()
        aes_count = AuditableEvent.objects.count()

        data = CreateProjectFormDataFactory()

        if missing_data == "empty":
            if field == "orgs":
                data[field] = []
            else:
                data[field] = ""
        else:
            data.pop(field, None)

        client.force_login(user)

        response = client.post(reverse("staff:project-create"), data)

        assert response.status_code == 200
        form = response.context_data["form"]
        assert form.is_bound
        assert field in form.errors

        assert Project.objects.count() == projects_count

        assert AuditableEvent.objects.count() == aes_count

        assert len(slack_messages) == 0

    def test_projectcreated_unauthorised(self, client, staff_area_administrator):
        user = staff_area_administrator

        client.force_login(user)

        response = client.post(
            reverse("staff:project-created", kwargs={"slug": "new-project-slug"})
        )
        assert response.status_code == 403


class TestProjectDetail:
    """Tests of the project detail view."""

    @pytest.mark.parametrize(
        "user_is_service_administrator",
        [True, False],
    )
    def test_projectdetail_authorized(self, client, user_is_service_administrator):
        """
        Test that a user with permission can access the ProjectDetail view.

        Parametrised to test that the Link Application content is only shown
        to ServiceAdministrators.
        """
        roles = (
            [StaffAreaAdministrator, ServiceAdministrator]
            if user_is_service_administrator
            else [StaffAreaAdministrator]
        )
        user = UserFactory(roles=roles)
        project = ProjectFactory()

        client.force_login(user)

        response = client.get(
            reverse("staff:project-detail", kwargs={"slug": project.slug})
        )
        assert response.status_code == 200
        # This class exists only to help automated testing that the content is as expected.
        assert "test-project-information-card" in response.text
        # This class exists only to help automated testing that the content is as expected.
        # It should only be appear if the user is a ServiceAdministrator.
        assert (
            "test-link-application" in response.text
        ) == user_is_service_administrator

    def test_projectdetail_unauthorized(self, client):
        """
        Test that a user without permission cannot access the ProjectDetail view.
        """
        project = ProjectFactory()

        response = client.get(
            reverse("staff:project-detail", kwargs={"slug": project.slug})
        )

        assert response.status_code == 403
