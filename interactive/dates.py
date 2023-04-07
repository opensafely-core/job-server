import calendar
from datetime import date, timedelta


def date_of_last_extract() -> date:
    # The cutoff for TPP's data extract is the Wednesday of the previous week
    # We usually receive the data on a Tuesday, so if today is a Tuesday or
    # Wednesday the cutoff is last Wednesday, otherwise it's the Wednesday before.
    today = date.today()

    offset = (today.weekday() - calendar.WEDNESDAY) % 7

    weeks = 0 if offset == 6 else 1

    return today - timedelta(days=offset, weeks=weeks)


def end_date(date) -> date:
    """
    Build an end date, rounding it to the last complete month

    As we're grouping by month we want to only look at months which we have
    all the data for.
    """
    _, day_count = calendar.monthrange(date.year, date.month)

    if date.day == day_count:
        return date

    # step back to the previous month
    # we need to get the year, month, and day calculated before updating so we
    # don't create an invalid Date object
    new_month = 12 if date.month == 1 else date.month - 1
    new_year = date.year - 1 if date.month == 1 else date.year

    # get the days in the target month from the values we've just created
    _, day_count = calendar.monthrange(new_year, new_month)

    # finally update our date to the new values
    return date.replace(year=new_year, month=new_month, day=day_count)


START_DATE = "2019-09-01"
END_DATE = end_date(date_of_last_extract()).strftime("%Y-%m-%d")
