import itertools
import re
from pathlib import Path


def test_all_icons(subtests):
    """Ensure icon tag names defined in templates are valid tags"""
    templates = [p for p in Path("templates").glob("**/*.html")]

    # remove templates with no icon tag so we can simplify the regex matching
    # code below
    icon_templates = [p for p in templates if "{% icon_" in p.read_text()]

    # look for the start of an icon templatetag and capture the full name
    icon_pat = re.compile(r"{% (icon_[^\s]+)")

    # get a set of icon names in the Django templates
    icons = set(
        itertools.chain.from_iterable(
            icon_pat.search(t.read_text()).groups() for t in icon_templates
        )
    )

    # read the component config contents into memory so we don't have to open
    # it for each icon
    config = Path("templates/components.yaml").read_text()
    for icon in icons:
        # use subtests to avoid failing the test at the first broken icon
        with subtests.test(icon=icon):
            assert icon in config
