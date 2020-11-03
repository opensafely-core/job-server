from django import template
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag
def status_icon(status_name):
    """Convert status strings to the relevant inline SVG."""

    status_lut = {
        "completed": {
            "color": "green",
            "name": "check.svg",
        },
        "running": {
            "color": "blue",
            "name": "spinner.svg",
        },
        "failed": {
            "color": "red",
            "name": "times.svg",
        },
        "pending": {
            "color": "grey",
            "name": "history.svg",
        },
    }
    default = {"color": "grey", "name": "question-circle.svg"}
    status = status_lut.get(status_name.lower(), default)

    spinner = ""
    if status_name.lower() == "running":
        spinner = 'class="spinner"'

    # Get the SVG file contents so we can put that directly into the template.
    # This lets us color the icons since they ship with fill="currentColor"
    # which takes a colour from the container element.
    path = finders.find(f"icons/{status['name']}")
    with open(path, "r") as f:
        svg = f.read()

    # Wrap to the SVG so we can style it neatly
    icon = f"""
    <div {spinner} style="color:{status['color']};width:16px;" title="{status_name}">
        {svg}
    </div>
    """

    return mark_safe(icon)
