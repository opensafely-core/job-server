from pathlib import Path

from django.test import override_settings

from applications.templatetags.snippet import snippet


@override_settings(BASE_DIR=Path(__file__).parents[2])
def test_snippet():
    output = snippet("test")
    assert output == "<h1>A Title</h1>\n<p>Some content</p>"
