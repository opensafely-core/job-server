import pytest

from jobserver.models import Backend
from staff.forms import UserForm


@pytest.mark.django_db
def test_userform_success():
    available_backends = Backend.objects.filter(slug__in=["emis", "tpp", "test"])

    data = {
        "backends": ["emis", "tpp"],
        "is_superuser": ["on"],
        "roles": [],
    }

    form = UserForm(
        available_backends=available_backends,
        available_roles=[],
        data=data,
    )

    assert form.is_valid(), form.errors

    output = set(form.cleaned_data["backends"].values_list("slug", flat=True))
    expected = set(
        Backend.objects.filter(slug__in=["emis", "tpp"]).values_list("slug", flat=True)
    )
    assert output == expected

    assert form.cleaned_data["is_superuser"]


@pytest.mark.django_db
def test_userform_with_no_backends():
    available_backends = Backend.objects.filter(slug__in=["tpp"])

    data = {
        "backends": [],
        "is_superuser": ["on"],
        "roles": [],
    }

    form = UserForm(
        available_backends=available_backends,
        available_roles=[],
        data=data,
    )

    assert form.is_valid()
    assert len(form.cleaned_data["backends"]) == 0


@pytest.mark.django_db
def test_userform_with_unknown_backend():
    available_backends = Backend.objects.filter(slug__in=["emis", "tpp", "test"])

    data = {
        "backends": ["emis", "tpp", "unknown"],
        "is_superuser": [""],
        "roles": [],
    }

    form = UserForm(
        available_backends=available_backends,
        available_roles=[],
        data=data,
    )

    assert not form.is_valid()
    assert form.errors == {
        "backends": [
            "Select a valid choice. unknown is not one of the available choices."
        ]
    }
