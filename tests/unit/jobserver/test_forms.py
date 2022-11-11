import pytest
from django.core.exceptions import ValidationError

from jobserver.backends import backends_to_choices
from jobserver.forms import JobRequestCreateForm, WorkspaceCreateForm
from jobserver.models import Backend

from ...factories import BackendFactory, WorkspaceFactory


def test_jobrequestcreateform_with_duplicate_name():
    WorkspaceFactory(name="test")

    data = {
        "name": "test",
        "repo": "test",
        "branch": "test",
        "purpose": "test",
    }
    repos_with_branches = [{"name": "test", "url": "test", "branches": ["test"]}]
    form = WorkspaceCreateForm(repos_with_branches, data)
    form.is_valid()

    assert form.errors == {
        "name": [
            'A workspace with the name "test" already exists, please choose a unique one.'
        ]
    }


def test_jobrequestcreateform_with_single_backend():
    backend = BackendFactory()
    choices = backends_to_choices([backend])
    form = JobRequestCreateForm({"backend": backend.slug}, backends=choices)

    assert "backend" in form.fields
    assert form.fields["backend"].choices == choices

    assert form.is_valid, form.errors


def test_jobrequestcreateform_with_multiple_backends():
    choices = backends_to_choices(Backend.objects.all())
    form = JobRequestCreateForm({"backend": "tpp"}, backends=choices)

    assert "backend" in form.fields
    assert form.fields["backend"].choices == choices

    assert form.is_valid, form.errors


def test_workspacecreateform_success():
    data = {
        "name": "test",
        "db": "slice",
        "repo": "http://example.com/derp/test-repo",
        "branch": "test-branch",
        "purpose": "test",
    }
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch"],
        }
    ]
    form = WorkspaceCreateForm(repos_with_branches, data)

    assert form.is_valid()


def test_workspacecreateform_success_with_upper_case_names():
    data = {
        "name": "TeSt",
        "db": "full",
        "repo": "http://example.com/derp/test-repo",
        "branch": "test-branch",
        "purpose": "test",
    }
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch"],
        }
    ]
    form = WorkspaceCreateForm(repos_with_branches, data)

    assert form.is_valid()
    assert form.cleaned_data["name"] == "test", form.cleaned_data["name"]


def test_workspacecreateform_unknown_branch():
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch"],
        }
    ]
    form = WorkspaceCreateForm(repos_with_branches)
    form.cleaned_data = {
        "name": "test",
        "db": "slice",
        "repo": "http://example.com/derp/test-repo",
        "branch": "unknown-branch",
    }

    with pytest.raises(ValidationError) as e:
        form.clean()

    assert e.value.message.startswith("Unknown branch")


def test_workspacecreateform_unknown_repo():
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch"],
        }
    ]
    form = WorkspaceCreateForm(repos_with_branches)
    form.cleaned_data = {
        "name": "test",
        "db": "full",
        "repo": "unknown-repo",
        "branch": "test-branch",
    }

    with pytest.raises(ValidationError) as e:
        form.clean()

    assert e.value.message.startswith("Unknown repo")
