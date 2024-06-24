import pytest
from bs4 import BeautifulSoup

from jobserver.reports import process_html


def normalize(html):
    return BeautifulSoup(html.strip(), "html.parser").prettify()


def assert_html_equal(actual, expected):
    assert normalize(actual) == normalize(expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "html",
    [
        """
        <!DOCTYPE html>
        <html>
            <head>
                <style type="text/css">body {margin: 0;}</style>
                <style type="text/css">a {background-color: red;}</style>
                <script src="https://a-js-package.js"></script>
            </head>
            <body>
                <p>foo</p>
                <div>Stuff</div>
            </body>
        </html>
        """,
        """
        <html>
            <body>
                <p>foo</p>
                <div>Stuff</div>
            </body>
        </html>
        """,
        """
        <p>foo</p>
        <div>Stuff</div>
        """,
        """
        <script>Some Javascript nonsense</script>
        <p>foo</p>
        <div>
            Stuff
            <script>Some more Javascript nonsense</script>
        </div>
        """,
        """
        <p onclick="alert('BOOM!')">foo</p>
        <div>
            Stuff
        </div>
        """,
        """
        <style>Mmmm, lovely styles...</style>
        <p>foo</p>
        <div>
            Stuff
            <style>MOAR STYLZ</style>
        </div>
        """,
        """
        <p style="color: red;">foo</p>
        <div>
            Stuff
            <style>MOAR STYLZ</style>
        </div>
        """,
    ],
    ids=[
        "Extracts body from HTML full document",
        "Extracts body from HTML document without head",
        "Returns HTML without body tags unchanged",
        "Strips out all script tags",
        "Strips out inline handlers",
        "Strips out all style tags",
        "Strips out inline styles",
    ],
)
def test_html_processing_extracts_body(html):
    expected = """
    <p>foo</p>
    <div>Stuff</div>
    """

    assert_html_equal(process_html(html), expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("input_html", "expected"),
    [
        (
            """
            <table>
                <tbody><tr><td>something</td></tr></tbody>
            </table>
            """,
            """
            <div class="overflow-wrapper">
                <table>
                    <tbody><tr><td>something</td></tr></tbody>
                </table>
            </div>
            """,
        ),
        (
            """
            <html>
                <body>
                    <table>
                        <tbody><tr><td>something</td></tr></tbody>
                    </table>
                </body>
            </html>
            """,
            """
            <div class="overflow-wrapper">
                <table>
                    <tbody><tr><td>something</td></tr></tbody>
                </table>
            </div>
            """,
        ),
        (
            """
            <table>
                <tbody><tr><td>something</td></tr></tbody>
            </table>
            <table>
                <tr><td>something else</td></tr>
            </table>
            """,
            """
            <div class="overflow-wrapper">
                <table>
                    <tbody><tr><td>something</td></tr></tbody>
                </table>
            </div>
            <div class="overflow-wrapper">
                <table>
                    <tbody><tr><td>something else</td></tr></tbody>
                </table>
            </div>
            """,
        ),
        (
            """
            <pre>Some code or something here</pre>
            """,
            """
            <div class="overflow-wrapper">
                <pre>Some code or something here</pre>
            </div>
            """,
        ),
    ],
    ids=[
        "Wraps single table in overflow wrappers",
        "Wraps table in full document in overflow wrappers",
        "Wraps multiple tables in overflow wrappers",
        "Wraps <pre> elements in overflow wrappers",
    ],
)
def test_html_processing_wraps_scrollables(input_html, expected):
    html = process_html(input_html)
    assert_html_equal(html, expected)
