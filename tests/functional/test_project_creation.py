import pytest
from playwright.sync_api import expect

from jobserver.authorization.roles import (
    ServiceAdministrator,
    StaffAreaAdministrator,
)


pytestmark = pytest.mark.functional


def test_can_create_a_project(login_context_for_user, page, live_server):
    """
    Test that a user with permission can successfully create a new project.

    * A user with the necassary permissions can login to jobserver and navigate to the Staff Area Projects page.
    * From here they can:
        * See and click the 'Create a project' button on the Staff Area Projects page
        * Navigate to ProjectCreateForm
        * See some text about the data their project will automatically be created with
        * See an empty form
        * Fill in the form with valid data and (name, number, pick org from multiselect, choose copilot) and submit the form
        * Be successfully redirected to the Project Created page, which:
            * Shows the name and number for the new project
            * Has staff area and main site links to the new project + a button to add members
    * Following successful project creation, the user can view an Audit Log entry for the new project
    """

    context, user = login_context_for_user(
        [ServiceAdministrator, StaffAreaAdministrator]
    )

    page = context.new_page()

    # Navigate to the Staff Area Projects page, click the "Create a project" button
    page.goto(f"{live_server.url}/staff/projects")

    expect(page.get_by_role("link", name="Create a project")).to_be_visible()
    page.get_by_role("link", name="Create a project").click()

    # Navigate to ProjectCreateForm
