from django.utils import timezone


def backends_to_choices(backends):
    return [(b.slug, b.name) for b in backends]


def show_warning(last_seen, threshold):
    """
    Should we show a warning for a backend?

    This is a helper function that takes a datetime (last_seen) and a threshold
    (timedelta) and returns a boolean for whether the datetime was more than
    threshold ago.

    This is a function because last_seen is a midly-complex lookup from the
    Stats table and we don't want to hid that on a model method.
    """
    if last_seen is None:
        return False

    delta = timezone.now() - last_seen

    if delta < threshold:
        return False
    return True
