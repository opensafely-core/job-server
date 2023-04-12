from datetime import date

import pytest

from interactive.dates import date_of_last_extract, end_date


def test_date_of_last_extract_mon_to_previous_wed(freezer):
    freezer.move_to("2022-05-16")
    assert date_of_last_extract() == date(2022, 5, 4)


def test_date_of_last_extract_sun_to_previous_wed(freezer):
    freezer.move_to("2022-05-15")
    assert date_of_last_extract() == date(2022, 5, 4)


def test_date_of_last_extract_thurs_to_previous_wed(freezer):
    freezer.move_to("2022-05-19")
    assert date_of_last_extract() == date(2022, 5, 11)


def test_date_of_last_extract_tues_to_previous_wed(freezer):
    freezer.move_to("2022-05-17")
    assert date_of_last_extract() == date(2022, 5, 11)


def test_date_of_last_extract_wed_to_previous_wed(freezer):
    freezer.move_to("2022-05-18")
    assert date_of_last_extract() == date(2022, 5, 11)


@pytest.mark.parametrize(
    "last_extract,expected",
    [
        (date(2023, 4, 6), date(2023, 3, 31)),
        (date(2023, 5, 31), date(2023, 5, 31)),
        (date(2020, 3, 12), date(2020, 2, 29)),
        (date(2023, 1, 7), date(2022, 12, 31)),
    ],
    ids=[
        "april -> may",
        "no change",
        "march -> leap february",
        "january -> previous year",
    ],
)
def test_end_date(last_extract, expected):
    assert end_date(last_extract) == expected
