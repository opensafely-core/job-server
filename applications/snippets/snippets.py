from django.conf import settings
from django.utils.safestring import mark_safe
from markdown import markdown


def render_snippet(key):
    path = settings.BASE_DIR / "applications" / "snippets" / "content" / f"{key}.md"
    text = path.read_text()
    content = markdown(text)
    return mark_safe(content)
