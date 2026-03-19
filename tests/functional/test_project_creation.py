from datetime import date

import pytest
from playwright.sync_api import expect

from jobserver.authorization.roles import (
    ServiceAdministrator,
    StaffAreaAdministrator,
)
from tests.factories import CreateProjectFormDataFactory


pytestmark = pytest.mark.functional


def test_can_create_a_project(login_context_for_user, page, live_server):
    """
    Test that a user with permission can successfully create a new project.

    * A user with the necassary permissions can login to jobserver and navigate to the Staff Area Projects page.
    * From here they can:
        * See and click the 'Create a project' button on the Staff Area Projects page
        * Navigate to ProjectCreateForm
        * See some metadata that their project will automatically be created with
        * See an empty form
        * Fill in the form with valid data and (name, number, pick an org, choose a copilot)
        * Submit the form
        * Be successfully redirected to the Project Created page, which:
            * Shows the name and number for the new project
            * Has staff area and main site links to the new project + a button to add members
    * Following successful project creation, the user can view an Audit Log entry for the new project
    """

    browser_context, user = login_context_for_user(
        [ServiceAdministrator, StaffAreaAdministrator]
    )

    page = browser_context.new_page()

    # create the form data before we load the page, so the org and
    # copilot exist when Django renders the form later int he test
    form_data = CreateProjectFormDataFactory()

    # Go to the Staff Area Projects page, click the "Create a project" button
    page.goto(f"{live_server.url}/staff/projects")

    # Click the "Create a project" button and go to ProjectCreateForm
    expect(page.get_by_role("link", name="Create a project")).to_be_visible()
    page.get_by_role("link", name="Create a project").click()
    expect(
        page.get_by_role("heading", name="Create a project", level=1)
    ).to_be_visible()

    # See correct meta data for new project in text above the form
    # (status is always set to Ongoing so we don't check this)
    # Created by: < user >  |  Created at: <today's date>
    metadata = page.locator("section").filter(
        has_text="When created, this project will automatically be saved with the following data:"
    )
    expect(metadata).to_contain_text(f"Created by: {user.fullname}")
    expect(metadata).to_contain_text(f"Created at: {date.today().strftime('%d/%m/%Y')}")
    expect(metadata).to_contain_text("Status: Ongoing")

    # See an empty form with a link to create a new org
    form = page.locator("form")
    number_input = form.get_by_label("Project ID")
    name_input = form.get_by_label("Project title")
    org_select = form.get_by_label("Link project to an organisation")
    copilot_select = form.get_by_label("Project Co-pilot")

    expect(number_input).to_contain_text("")
    expect(name_input).to_contain_text("")
    expect(form.get_by_role("link", name="add a new org")).to_be_visible()
    expect(org_select).to_contain_text("")
    expect(copilot_select.locator("option:checked")).to_have_text("---------")

    # Insert valid data into form and submit
    name_input.fill(form_data["name"])
    number_input.fill(form_data["number"])
    org_select.select_option(value=form_data["orgs"])
    copilot_select.select_option(value=form_data["copilot"])
    form.get_by_role("button", name="Save").click()
