from datetime import timedelta


def minutes_ago(now, minutes):
    return now - timedelta(minutes=minutes)


def seconds_ago(now, seconds):
    return now - timedelta(seconds=seconds)
