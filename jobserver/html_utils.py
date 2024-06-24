import nh3


def clean_html(html):
    """
    Cleans the given HTML document/fragment with a whitelist-based cleaner, returning an
    HTML fragment that conforms to the HTML5 specification.
    """
    cleaned = nh3.clean(html)
    return cleaned
