from datetime import timedelta


def minutes_ago(now, minutes):
    return now - timedelta(minutes=minutes)
