import itertools
import re
from pathlib import Path

import pytest


# Logically, this feels like it could be a pytest.fixture.
# However, it's not currently possible to use fixtures with parametrize:
# https://github.com/pytest-dev/pytest/issues/349
def icons():
    templates = [p for p in Path("templates").glob("**/*.html")]

    # Remove templates with no icon tag so we can simplify the regex matching
    # code below.
    icon_templates = [p for p in templates if "{% icon_" in p.read_text()]

    # Look for the start of an icon templatetag and capture the full name.
    icon_pat = re.compile(r"{% (icon_[^\s]+)")

    # Get a sorted list of non-duplicated icon names in the Django templates.
    # We use a sorted list instead of only a set
    # to make this test work with parametrize and xdist:
    # https://pytest-xdist.readthedocs.io/en/stable/known-limitations.html#order-and-amount-of-test-must-be-consistent
    icons = sorted(
        set(
            itertools.chain.from_iterable(
                icon_pat.search(t.read_text()).groups() for t in icon_templates
            )
        )
    )

    return icons


@pytest.fixture(scope="module")
def component_config():
    # This is scoped to ideally to read the component config contents once,
    # so we don't have to read it for each icon.
    # Note: this fixture does not get reused with pytest-xdist,
    # but in our case does not have any ill effect apart from duplicating work.
    # https://github.com/pytest-dev/pytest-xdist/issues/783
    return Path("templates/components.yaml").read_text()


@pytest.mark.parametrize("icon", icons())
def test_all_icons(icon, component_config):
    """Ensure icon tag names defined in templates are valid tags"""
    assert icon in component_config
