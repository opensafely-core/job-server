import pytest
from django.core.exceptions import ValidationError

from jobserver.forms import JobRequestCreateForm, WorkspaceCreateForm


def test_jobrequestcreateform_all_backends():
    form = JobRequestCreateForm(data="", actions=["test"])
    form.cleaned_data = {"backends": "all"}

    output = form.clean_backends()
    assert output == ["emis", "tpp"]


def test_jobrequestcreateform_one_backend():
    form = JobRequestCreateForm(actions=["test"])
    form.cleaned_data = {"backends": "tpp"}

    output = form.clean_backends()
    assert output == ["tpp"]


def test_jobrequestcreateform_unknown_backend():
    form = JobRequestCreateForm(actions=["test"])
    form.cleaned_data = {"backends": "test"}

    with pytest.raises(ValidationError):
        form.clean_backends()


def test_workspacecreateform_success():
    data = {
        "name": "test",
        "db": "dummy",
        "repo": "http://example.com/derp/test-repo",
        "branch": "test-branch",
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
        "db": "dummy",
        "repo": "http://example.com/derp/test-repo",
        "branch": "unknown-branch",
    }

    with pytest.raises(ValidationError) as e:
        form.clean_branch()

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
        "db": "dummy",
        "repo": "unknown-repo",
        "branch": "test-branch",
    }

    with pytest.raises(ValidationError) as e:
        form.clean_branch()

    assert e.value.message.startswith("Unknown repo")
