from bs4 import BeautifulSoup
from django.utils.safestring import mark_safe

from jobserver import html_utils


def process_html(html):
    # We want to handle complete HTML documents and also fragments. We're going to extract the contents of the body
    # at the end of this function, but it's easiest to normalize to complete documents because that's what the
    # HTML-wrangling libraries we're using are most comfortable handling.
    if "<html>" not in html:
        html = f"<html><body>{html}</body></head>"

    cleaned = html_utils.clean_html(html)

    soup = BeautifulSoup(cleaned, "html.parser")

    # For small screens we want to allow side-scrolling for just a small number of elements. To enable this each one
    # needs to be wrapped in a div that we can target for styling.
    for tag in ["table", "pre"]:
        for element in soup.find_all(tag):
            element.wrap(soup.new_tag("div", attrs={"class": "overflow-wrapper"}))

    body_content = "".join([str(element) for element in soup.body.contents])
    return mark_safe(body_content)
