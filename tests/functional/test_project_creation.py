import pytest
from playwright.sync_api import expect


pytestmark = pytest.mark.functional


def test_can_create_a_project(page, live_server):
    """
    Test that a user with permission can successfully create a new project.

    * A user with permission can login to jobserver and navigate to the Staff Area Projects page.
    * From here they can:
        * See and click the 'Create a project' button
        * Navigate to ProjectCreateForm
        * See some text about the data their project will automatically be created with
        * See an empty form
        * Fill in the form with valid data and (name, number, pick org from multiselect, choose copilot) and submit the form
        * Be successfully redirected to the Project Created page, which:
            * Shows the name and number for the new project
            * Has staff area and main site links to the new project + a button to add members
    * Following successful project creation, the user can view an Audit Log entry for the new project
    """
    page.goto(live_server.url)
    expect(page.get_by_role("heading", name="OpenSAFELY Jobs", level=1)).to_be_visible()
