import inspect

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.urls import reverse
from django.utils import timezone

from redirects.models import Redirect, validate_not_empty

from ... import factories
from ...factories import ProjectFactory, RedirectFactory, UserFactory


def get_factory(model):
    """Find the factory for the given model object"""
    classes = [value for name, value in inspect.getmembers(factories, inspect.isclass)]
    all_factories = [c for c in classes if c.__name__.endswith("Factory")]

    return next(  # pragma: no branch
        (f for f in all_factories if f._meta.model == model), None
    )


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


def test_redirect_constraints_deleted_at_and_deleted_by_both_set():
    RedirectFactory(
        project=ProjectFactory(),
        old_url="/test/",
        deleted_at=timezone.now(),
        deleted_by=UserFactory(),
    )


def test_redirect_constraints_deleted_at_and_deleted_by_neither_set():
    RedirectFactory(
        project=ProjectFactory(), old_url="/test/", deleted_at=None, deleted_by=None
    )


@pytest.mark.django_db(transaction=True)
def test_redirect_constraints_deleted_at_and_deleted_by_only_one_set():
    with pytest.raises(IntegrityError):
        RedirectFactory(
            project=ProjectFactory(),
            old_url="/test/",
            deleted_at=timezone.now(),
            deleted_by=None,
        )

    with pytest.raises(IntegrityError):
        RedirectFactory(
            project=ProjectFactory(),
            old_url="/test/",
            deleted_at=None,
            deleted_by=UserFactory(),
        )


def test_redirect_constraints_old_url_empty():
    with pytest.raises(IntegrityError):
        RedirectFactory(project=ProjectFactory(), old_url="")


@pytest.mark.parametrize("url", ["test", "/test", "test/"])
def test_redirect_constraints_old_url_has_leading_and_trailing_slashes(url):
    with pytest.raises(IntegrityError):
        RedirectFactory(project=ProjectFactory(), old_url=url)


def test_redirect_each_target_object():
    """
    Test each redirect target one at a time

    We could do this manually but the expectation is that we'll add more
    targets over time and we don't want to avoid testing those by accident.
    """
    for field in get_target_fields():
        kwargs = {field.name: get_factory(field.related_model)()}
        RedirectFactory(**kwargs)


def test_redirect_get_staff_url():
    redirect = RedirectFactory(project=ProjectFactory())

    url = redirect.get_staff_url()

    assert url == reverse("staff:redirect-detail", kwargs={"pk": redirect.pk})


def test_redirect_get_staff_delete_url():
    redirect = RedirectFactory(project=ProjectFactory())

    url = redirect.get_staff_delete_url()

    assert url == reverse("staff:redirect-delete", kwargs={"pk": redirect.pk})


def test_redirect_no_target_objects():
    with pytest.raises(IntegrityError):
        RedirectFactory()


def test_redirect_obj():
    """
    Ensure Redirect.obj can point to any of the target FKs

    The Redirect model has several ForeignKeys to objects which need redirects,
    and some for auditing.  The .obj property provides a way for users to get
    the target of a given Redirect.  This test ensures we've not missed any
    fields in that property.
    """

    for field in Redirect.targets():
        factory_name = f"{field.related_model.__name__}Factory"
        factory = getattr(factories, factory_name)()

        redirect = RedirectFactory(old_url="/test/", **{field.name: factory})
        assert redirect.obj


def test_redirect_str():
    redirect = RedirectFactory(project=ProjectFactory(), old_url="/testing/foo/")

    assert str(redirect) == "/testing/foo/"


def test_validate_not_empty():
    assert validate_not_empty("test") is None


def test_validate_not_empty_with_content():
    validate_not_empty("test")


def test_validate_not_empty_without_content():
    with pytest.raises(ValidationError):
        validate_not_empty("")

    with pytest.raises(ValidationError):
        validate_not_empty(None)
