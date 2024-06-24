import nh3


def clean_html(html):
    """
    Cleans the given HTML document/fragment with a whitelist-based cleaner, returning an
    HTML fragment that conforms to the HTML5 specification.
    """
    return nh3.clean(html)
