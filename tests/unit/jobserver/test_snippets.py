from pathlib import Path

from django.test import override_settings

from jobserver.snippets import render_snippet


@override_settings(BASE_DIR=Path(__file__).parent)
def test_render_snippet():
    output = render_snippet("test")
    assert hasattr(output, "__html__")
    assert output == "<h1>A Title</h1>\n<p>Some content</p>"
