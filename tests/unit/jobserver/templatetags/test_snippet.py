import os

from django.conf import settings

from jobserver.templatetags.snippet import snippet


def test_snippet(monkeypatch):
    jobserver_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    monkeypatch.setattr(settings, "BASE_DIR", jobserver_dir)

    output = snippet("test")

    assert output == "<h1>A Title</h1>\n<p>Some content</p>"
