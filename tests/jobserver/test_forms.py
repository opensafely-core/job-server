import pytest
from django.core.exceptions import ValidationError

from jobserver.forms import JobRequestCreateForm


def test_jobrequestcreateform_all_backends():
    form = JobRequestCreateForm("")
    form.cleaned_data = {"backends": "all"}

    output = form.clean_backends()
    assert output == ["emis", "tpp"]


def test_jobrequestcreateform_one_backend():
    form = JobRequestCreateForm()
    form.cleaned_data = {"backends": "tpp"}

    output = form.clean_backends()
    assert output == ["tpp"]


def test_jobrequestcreateform_unknown_backend():
    form = JobRequestCreateForm()
    form.cleaned_data = {"backends": "test"}

    with pytest.raises(ValidationError):
        form.clean_backends()
