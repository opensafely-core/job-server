from lxml.html.clean import Cleaner


def clean_html(html):
    cleaned = Cleaner(page_structure=False, style=True, kill_tags=["head"]).clean_html(
        html
    )
    return cleaned
