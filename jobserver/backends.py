from datetime import timedelta

from django.utils import timezone
from environs import Env


env = Env()


available_backends = {
    "emis",
    "expectations",
    "tpp",
}


def get_configured_backends():
    """Get a list of configured Backends from the env"""
    backends = env.list("BACKENDS", default=[])

    # remove whitespace and only return non-empty strings
    backends = {u.strip() for u in backends if u}

    unknown = backends - available_backends
    if unknown:
        sorted_unknown = sorted(unknown)
        raise Exception(f"Unknown backends: {', '.join(sorted_unknown)}")

    return backends


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
