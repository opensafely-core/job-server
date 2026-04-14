import pytest
from django.urls import reverse
from playwright.sync_api import expect

from jobserver.authorization.permissions import Permission
from jobserver.models import Org, Project
from tests.factories import CreateProjectFormDataFactory
from tests.functional.utils import login_user


pytestmark = pytest.mark.functional


def test_can_create_a_project(
    context,
    client,
    page,
    live_server,
    slack_messages,
    role_factory,
    freezer,
    potential_copilots,
):
    """
    Test that a user with the necessary permissions can successfully create a new project by interacting with the UI through their browser.
    """
    freezer.move_to("2026-04-02 08:00")
    # Create a user with permissions to view the Staff Area ProjectList view,
    # the "Create a project" button, ProjectCreate, ProjectCreated and OrgCreate views
    user = login_user(
        context=context,
        client=client,
        live_server=live_server,
        roles=[
            role_factory(permission=Permission.STAFF_AREA_ACCESS),
            role_factory(permission=Permission.PROJECT_CREATE),
            role_factory(permission=Permission.ORG_CREATE),
        ],
    )

    # Create the form input data before we load the page, so the copilot User instance
    # exists in the db, and can be used in the copilot select form field later in the test
    form_data = CreateProjectFormDataFactory(copilot=str(potential_copilots.first().pk))

    # Go to the Staff Area Projects page
    page.goto(f"{live_server.url}{reverse('staff:project-list')}")

    # Click "Create a project" button (only visible to those with Permission.PROJECT_CREATE),
    # go to ProjectCreate page and see correct meta data for new project in text above form
    expect(page.get_by_role("link", name="Create a project")).to_be_visible()
    page.get_by_role("link", name="Create a project").click()

    expect(page).to_have_url(f"{live_server.url}{reverse('staff:project-create')}")
    metadata = page.locator("section").filter(
        has_text="When created, this project will automatically be saved with the following data:"
    )
    expect(metadata).to_contain_text(f"Created by: {user.fullname}")
    # We don't control the time/date in this test, so this assertion may fail if run close to midnight
    expect(metadata).to_contain_text("Created at: 02/04/2026")
    expect(metadata).to_contain_text("Status: Ongoing")

    # See an empty form with a link to create a new org
    form = page.locator("form")
    number_input = form.get_by_label("Project ID")
    name_input = form.get_by_label("Project title")
    org_select = form.get_by_label("Link project to an organisation")
    create_org_link = form.get_by_role("link", name="add a new org")
    copilot_select = form.get_by_label("Project Co-pilot")

    expect(number_input).to_have_value("")
    expect(name_input).to_have_value("")
    # only visible because we have permission to create an org
    expect(create_org_link).to_be_visible()
    expect(org_select.locator("option:checked")).to_have_text("---------")
    expect(copilot_select.locator("option:checked")).to_have_text("---------")

    # Click "add a new org" link, go to org create form, create new org for project
    create_org_link.click()
    expect(page).to_have_url(
        f"{live_server.url}{reverse('staff:org-create')}?next={reverse('staff:project-create')}"
    )
    form.get_by_label("Organisation name").fill("A new org")
    form.get_by_role("button", name="Add org").click()

    # We're redirected back to the project creation form and see the
    # org field is populated with the org we just created
    new_org = Org.objects.get(name="A new org")
    expect(page).to_have_url(
        f"{live_server.url}{reverse('staff:project-create')}?org-slug={new_org.slug}"
    )
    expect(org_select.locator("option:checked")).to_have_text(new_org.name)

    # Insert valid data into form and submit
    name_input.fill(form_data["name"])
    number_input.fill(form_data["number"])
    copilot_select.select_option(value=form_data["copilot"])
    form.get_by_role("button", name="Save").click()

    new_project = Project.objects.first()

    # Successfully redirect to the Project Created page
    expect(page).to_have_url(
        f"{live_server.url}{reverse('staff:project-created', kwargs={'slug': new_project.slug})}"
    )

    # Check Project Created page displays the new project name and number,
    # the links to the new project, and a button to add project members
    expect(
        page.get_by_text(f"{new_project.number}: {new_project.name}")
    ).to_be_visible()
    expect(page.get_by_role("link", name="View project on Job Server")).to_be_visible()
    expect(
        page.get_by_role("link", name="View project on Job Server")
    ).to_have_attribute("href", new_project.get_absolute_url())
    expect(
        page.get_by_role("link", name="View project in the Staff Area")
    ).to_be_visible()
    expect(
        page.get_by_role("link", name="View project in the Staff Area")
    ).to_have_attribute("href", new_project.get_staff_url())
    expect(page.get_by_role("link", name="Add members to project →")).to_be_visible()
    expect(page.get_by_role("link", name="Add members to project →")).to_have_attribute(
        "href", reverse("staff:project-add-member", kwargs={"slug": new_project.slug})
    )
