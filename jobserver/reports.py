from bs4 import BeautifulSoup
from django.utils.safestring import mark_safe

from jobserver import html_utils


def process_html(html):
    cleaned = html_utils.clean_html(html)

    # It's easier for BeautifulSoup to work with an HTML document, rather than with an
    # HTML fragment.
    cleaned = f"<html><body>{cleaned}</body></head>"

    soup = BeautifulSoup(cleaned, "html.parser")

    # For small screens we want to allow side-scrolling for just a small number of elements. To enable this each one
    # needs to be wrapped in a div that we can target for styling.
    for tag in ["table", "pre"]:
        for element in soup.find_all(tag):
            element.wrap(soup.new_tag("div", attrs={"class": "overflow-wrapper"}))

    body_content = "".join([str(element) for element in soup.body.contents])
    return mark_safe(body_content)
