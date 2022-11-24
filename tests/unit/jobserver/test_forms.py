import pytest
from django.core.exceptions import ValidationError

from jobserver.backends import backends_to_choices
from jobserver.forms import JobRequestCreateForm, WorkspaceCreateForm
from jobserver.models import Backend

from ...factories import BackendFactory, ProjectFactory, RepoFactory, WorkspaceFactory


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
    project = ProjectFactory()
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
    form = WorkspaceCreateForm(project, repos_with_branches, data)

    assert form.is_valid()


def test_workspacecreateform_success_with_upper_case_names():
    project = ProjectFactory()
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
    form = WorkspaceCreateForm(project, repos_with_branches, data)

    assert form.is_valid()
    assert form.cleaned_data["name"] == "test", form.cleaned_data["name"]


def test_workspacecreateform_unknown_branch():
    project = ProjectFactory()
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch"],
        }
    ]
    form = WorkspaceCreateForm(project, repos_with_branches)
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
    project = ProjectFactory()
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch"],
        }
    ]
    form = WorkspaceCreateForm(project, repos_with_branches)
    form.cleaned_data = {
        "name": "test",
        "db": "full",
        "repo": "unknown-repo",
        "branch": "test-branch",
    }

    with pytest.raises(ValidationError) as e:
        form.clean()

    assert e.value.message.startswith("Unknown repo")


def test_workspacecreateform_with_duplicate_name():
    project = ProjectFactory()
    WorkspaceFactory(name="test")

    data = {
        "name": "test",
        "repo": "test",
        "branch": "test",
        "purpose": "test",
    }
    repos_with_branches = [{"name": "test", "url": "test", "branches": ["test"]}]
    form = WorkspaceCreateForm(project, repos_with_branches, data)
    form.is_valid()

    assert form.errors == {
        "name": [
            'A workspace with the name "test" already exists, please choose a unique one.'
        ]
    }


def test_workspacecreateform_repo_used_in_another_project():
    project1 = ProjectFactory()
    project2 = ProjectFactory()
    repo = RepoFactory(url="test")
    WorkspaceFactory(project=project1, repo=repo)

    repos_with_branches = [
        {
            "name": "test",
            "url": "test",
            "branches": ["test-branch"],
        }
    ]
    data = {
        "name": "test",
        "repo": "test",
        "branch": "test-branch",
        "purpose": "test",
    }
    form = WorkspaceCreateForm(project2, repos_with_branches, data)
    form.is_valid()

    assert form.errors == {
        "repo": [
            "This repo has already been used in another project, please pick a different one"
        ]
    }


def test_workspacecreateform_repo_used_with_no_projects():
    project = ProjectFactory()
    repos_with_branches = [
        {
            "name": "test",
            "url": "test",
            "branches": ["test-branch"],
        }
    ]

    form = WorkspaceCreateForm(project, repos_with_branches, {"repo": "test"})
    form.cleaned_data = {"repo": "test"}

    assert form.clean_repo()


def test_workspacecreateform_repo_used_with_only_this_project():
    project = ProjectFactory()
    repo = RepoFactory(url="test")
    WorkspaceFactory(project=project, repo=repo)
    repos_with_branches = [
        {
            "name": "test",
            "url": "test",
            "branches": ["test-branch"],
        }
    ]

    form = WorkspaceCreateForm(project, repos_with_branches, {"repo": "test"})
    form.cleaned_data = {"repo": "test"}

    assert form.clean_repo()


def test_workspacecreateform_repo_used_with_this_and_other_projects():
    repo = RepoFactory(url="test")

    # an existing, different project
    project1 = ProjectFactory()
    WorkspaceFactory(project=project1, repo=repo)

    # the project we're working on
    project2 = ProjectFactory()
    WorkspaceFactory(project=project2, repo=repo)

    repos_with_branches = [
        {
            "name": "test",
            "url": "test",
            "branches": ["test-branch"],
        }
    ]

    form = WorkspaceCreateForm(project2, repos_with_branches, {"repo": "test"})
    form.cleaned_data = {"repo": "test"}

    assert form.clean_repo()
