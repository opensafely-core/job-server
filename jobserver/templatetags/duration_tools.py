from django import template


register = template.Library()


@register.filter
def duration(td):
    """
    Convert a timedelta into a more human readable string

    str(td) produces a reasonable output, "5 days, 11:05:42", where the days
    portion is only rendered if there is more than one day in the delta.
    However, the hours:minutes:seconds representation looks a lot like a time,
    making it slightly confusing in our context.

    This helper converts the given timedelta into the string "5 days 11h 5m
    42s", with each section only being rendered if it exists.
    """
    if not td:
        return "-"

    output = ""

    if td.days:
        output += f"{td.days} days "

    days, remaining_seconds = divmod(td.total_seconds(), 86400)
    hours, remaining_seconds = divmod(remaining_seconds, 3600)
    minutes, seconds = divmod(remaining_seconds, 60)

    if hours:
        output += f"{int(hours)} hours "

    if minutes:
        output += f"{int(minutes)} minutes "

    if seconds:
        output += f"{int(seconds)} seconds"

    return output.strip()
