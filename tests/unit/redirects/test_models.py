import inspect

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.urls import reverse
from first import first

from redirects.models import Redirect, validate_not_empty

from ... import factories
from ...factories import ProjectFactory, RedirectFactory


def get_factory(model):
    """Find the factory for the given model object"""
    classes = [value for name, value in inspect.getmembers(factories, inspect.isclass)]
    all_factories = [c for c in classes if c.__name__.endswith("Factory")]

    return first(all_factories, key=lambda m: m._meta.model == model)


def get_target_fields():
    """Find the FK fields we use to target objects for a redirect"""
    return [
        f
        for f in Redirect._meta.fields
        if isinstance(f, models.ForeignKey) and not f.name.endswith("_by")
    ]


def test_redirect_all_target_objects():
    """
    Try creating a RedirectFactory with every target FK filled

    We could do this manually but the expectation is that we'll add more
    targets over time and we don't want to avoid testing those by accident.
    """
    fields = get_target_fields()

    kwargs = {f.name: get_factory(f.related_model)() for f in fields}

    with pytest.raises(IntegrityError):
        RedirectFactory(**kwargs)


def test_redirect_each_target_object():
    """
    Test each redirect target one at a time

    We could do this manually but the expectation is that we'll add more
    targets over time and we don't want to avoid testing those by accident.
    """
    for field in get_target_fields():
        kwargs = {field.name: get_factory(field.related_model)()}
        RedirectFactory(**kwargs)


def test_redirect_no_target_objects():
    with pytest.raises(IntegrityError):
        RedirectFactory()


def test_redirect_get_staff_url():
    redirect = RedirectFactory(project=ProjectFactory())

    url = redirect.get_staff_url()

    assert url == reverse("staff:redirect-detail", kwargs={"pk": redirect.pk})


def test_redirect_get_staff_delete_url():
    redirect = RedirectFactory(project=ProjectFactory())

    url = redirect.get_staff_delete_url()

    assert url == reverse("staff:redirect-delete", kwargs={"pk": redirect.pk})


def test_validate_not_empty():
    assert validate_not_empty("test") is None

    with pytest.raises(ValidationError):
        validate_not_empty("")

    with pytest.raises(ValidationError):
        validate_not_empty(None)
