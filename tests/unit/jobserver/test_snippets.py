import os

from django.conf import settings

from jobserver.snippets import (
    build_path,
    expand_snippets,
    render_snippet,
    replace_value_with_snippet,
)


# expand_snippets
# replace_value_with_snippet
# build_path
# render_snippet


def test_build_path(monkeypatch):
    monkeypatch.setattr(settings, "BASE_DIR", "/base/path/")

    output = build_path("test")

    assert output == "/base/path/snippets/test.md"


def test_expand_snippets(monkeypatch):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    monkeypatch.setattr(settings, "BASE_DIR", this_dir)

    spec = {
        "key": 1,
        "title": "The Title",
        "sub_title": "The Sub Title",
        "rubric": "<snippet>",
        "fieldsets": [
            {
                "label": "<snippet>",
                "fields": [
                    {
                        "name": "full_name",
                        "label": "<snippet>",
                    },
                ],
            },
        ],
    }

    output = expand_snippets(spec)

    expected = {
        "key": 1,
        "title": "The Title",
        "sub_title": "The Sub Title",
        "rubric": "<p>A rubric from a snippet</p>",
        "fieldsets": [
            {
                "label": "<p>A fieldset label from a snippet</p>",
                "fields": [
                    {
                        "name": "full_name",
                        "label": "<p>A field label from a snippet</p>",
                    },
                ],
            },
        ],
    }

    assert output == expected


def test_render_snippet():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snippets/test.md")
    # make an in memory markdown file
    # assert output is HTML
    output = render_snippet(path)

    assert hasattr(output, "__html__")

    assert output == "<h1>A Title</h1>\n<p>Some content</p>"


def test_replace_value_with_snippet(monkeypatch):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    monkeypatch.setattr(settings, "BASE_DIR", this_dir)

    output = replace_value_with_snippet("test", "<snippet>")

    assert output == "<h1>A Title</h1>\n<p>Some content</p>"


def test_replace_value_with_snippet_without_placeholder():
    assert replace_value_with_snippet("name", "test") == "test"
