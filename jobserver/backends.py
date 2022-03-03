from datetime import timedelta

from django.utils import timezone


def backends_to_choices(backends):
    return [(b.slug, b.name) for b in backends]


def show_warning(last_seen, minutes=5):
    if last_seen is None:
        return False

    now = timezone.now()
    threshold = timedelta(minutes=minutes)
    delta = now - last_seen

    if delta < threshold:
        return False
    return True
