from datetime import timedelta

from django.utils import timezone


def show_warning(unacked, last_seen, minutes=5):
    if unacked == 0:
        return False

    if last_seen is None:
        return False

    now = timezone.now()
    threshold = timedelta(minutes=minutes)
    delta = now - last_seen

    if delta < threshold:
        return False

    return True
