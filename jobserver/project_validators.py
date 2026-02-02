import re

from django.core.exceptions import ValidationError


PROJECT_IDENTIFIER_PATTERN = re.compile(r"^POS-\d{4}-\d{4,}$", re.IGNORECASE)


def normalize_project_identifier(value):
    if value in (None, ""):
        return None

    return str(value).strip().upper()


def check_project_identifier_format(value):
    normalized = normalize_project_identifier(value)
    # some project does not have a project number
    if normalized is None:
        return True
    # new project numbers are still in numeric format
    if normalized.isdigit():
        return True
    return bool(PROJECT_IDENTIFIER_PATTERN.match(normalized.upper()))


def validate_project_identifier(value):
    normalized = normalize_project_identifier(value)
    if normalized is None:
        return

    if normalized.isdigit():
        return

    if PROJECT_IDENTIFIER_PATTERN.match(normalized):
        return

    raise ValidationError(
        "Use either a numeric ID or the new POS-YYYY-#### identifier."
    )
