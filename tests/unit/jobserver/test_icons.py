import re
from pathlib import Path

import pytest


# Logically, this feels like it could be a pytest.fixture.
# However, it's not currently possible to use fixtures with parametrize:
# https://github.com/pytest-dev/pytest/issues/349
def find_icon_tag_names_used():
    """Find the name of template tags starting with `icon_` used in our templates."""
    icon_pattern = re.compile(r"{% (icon_[^\s]+)")
    template_paths = list(Path("templates").rglob("*.html"))
    # Get a sorted list of all of the icon names in the Django template tags.
    # We use a sorted list so that the different xdist workers get a consistent ordering.
    # https://pytest-xdist.readthedocs.io/en/stable/known-limitations.html#order-and-amount-of-test-must-be-consistent
    return sorted(
        set(
            icon_tag_name
            for path in template_paths
            for icon_tag_name in icon_pattern.findall(path.read_text())
        )
    )


@pytest.fixture(scope="module")
def component_config():
    # Note: this fixture does not get reused with pytest-xdist,
    # so the file is read once per-worker, but this is very fast anyway.
    # https://github.com/pytest-dev/pytest-xdist/issues/783
    return Path("templates/components.yaml").read_text()


@pytest.mark.parametrize("icon_tag_name", find_icon_tag_names_used())
def test_icon_tag_names_config(icon_tag_name, component_config):
    """Ensure icon tag names defined in templates appear in the icon component
    configuration file."""
    assert icon_tag_name in component_config
