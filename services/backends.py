from django.conf import settings


# Available Backends
EMIS = "emis"
EXPECTATIONS = "expectations"
TPP = "tpp"

# Backends wrapped up for Django models/forms
BACKEND_CHOICES = [
    (EMIS, "EMIS"),
    (TPP, "TPP"),
]
# TODO: configure this via the environment
if settings.DEBUG:
    BACKEND_CHOICES.insert(0, (EXPECTATIONS, "Expectations"))
