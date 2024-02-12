import inspect

from django.apps import apps
from factory.django import DjangoModelFactory

from . import factories


_SKIP_APP_LABELS = {"auth", "contenttypes", "sessions", "social_django"}

_MODEL_TO_FACTORY = {
    f._meta.model: f
    for f in vars(factories).values()
    if inspect.isclass(f) and issubclass(f, DjangoModelFactory)
}


def get_models():
    """
    Return a list of all installed, project-specific models.
    """
    return [
        model
        for model in apps.get_models()
        if model._meta.app_label not in _SKIP_APP_LABELS
    ]


class MissingFactoryError(Exception):
    pass


def get_factory(model):
    try:
        return _MODEL_TO_FACTORY[model]
    except KeyError:  # pragma: no cover
        raise MissingFactoryError(f"{model._meta.label} is missing a factory")


def get_paired_fields(model, lsuffix, rsuffix, exclude=None):
    exclude = set() if exclude is None else set(exclude)
    names = [
        name for field in model._meta.fields if (name := field.name) not in exclude
    ]

    def get_stems(suffix):
        return {stem for name in names if (stem := name.removesuffix(suffix)) != name}

    lstems = get_stems(lsuffix)
    rstems = get_stems(rsuffix)
    # Sorting ensures that the list of paired fields is consistent between calls.
    stems = sorted(lstems & rstems)

    return [(f"{stem}{lsuffix}", f"{stem}{rsuffix}") for stem in stems]


def get_all_paired_fields(lsuffix, rsuffix, *, exclude=None):
    exclude = [] if exclude is None else exclude

    models = {model: [] for model in get_models()}
    for model_label, *field_names in exclude:
        model = apps.get_model(model_label)
        if field_names:
            models[model].extend(field_names)
        else:
            models.pop(model)

    for model, field_names in models.items():
        factory = get_factory(model)
        for lname, rname in get_paired_fields(model, lsuffix, rsuffix, field_names):
            yield factory, lname, rname


def get_optional_paired_fields(*args, **kwargs):
    for factory, lname, rname in get_all_paired_fields(*args, **kwargs):
        model = factory._meta.model
        lfield = model._meta.get_field(lname)
        rfield = model._meta.get_field(rname)
        if lfield.null and rfield.null:
            yield factory, lname, rname
