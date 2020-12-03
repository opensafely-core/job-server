from datetime import timedelta

from django.utils import timezone
from environs import Env


env = Env()


EMIS = "emis"
EXPECTATIONS = "expectations"
TPP = "tpp"
available_backends = {
    EMIS: "EMIS",
    EXPECTATIONS: "Expectations",
    TPP: "TPP",
}


def build_backends():
    """Get a list of requested Backends from the env"""
    backends = env.list("BACKENDS", default=["expectations"])

    # remove whitespace and only return non-empty strings
    backends = {u.strip() for u in backends if u}

    unknown = backends - set(available_backends.keys())
    if unknown:
        sorted_unknown = sorted(unknown)
        raise Exception(f"Unknown backends: {', '.join(sorted_unknown)}")

    return backends


backends = build_backends()


def build_choices(backends):
    """
    Build a Django-choices structure from the given backends
    """
    return [
        (name, label) for name, label in available_backends.items() if name in backends
    ]


BACKEND_CHOICES = build_choices(backends)


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
