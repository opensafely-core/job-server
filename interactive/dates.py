from calendar import WEDNESDAY
from datetime import date, timedelta


def date_of_last_extract():
    # The cutoff for TPP's data extract is the Wednesday of the previous week
    # We usually receive the data on a Tuesday, so if today is a Tuesday or
    # Wednesday the cutoff is last Wednesday, otherwise it's the Wednesday before.
    today = date.today()

    offset = (today.weekday() - WEDNESDAY) % 7

    weeks = 0 if offset == 6 else 1

    return today - timedelta(days=offset, weeks=weeks)


# Temporarily change this to look at the last six months while testing
START_DATE = (date_of_last_extract() - timedelta(days=30 * 6)).strftime("%Y-%m-%d")
END_DATE = date_of_last_extract().strftime("%Y-%m-%d")
