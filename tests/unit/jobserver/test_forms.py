import pytest
from django.core.exceptions import ValidationError

from jobserver.backends import backends_to_choices
from jobserver.forms import JobRequestCreateForm, WorkspaceCreateForm
from jobserver.models import Backend

from ...factories import BackendFactory, WorkspaceFactory


def test_jobrequestcreateform_with_single_backend():
    backend = BackendFactory()
    choices = backends_to_choices([backend])
    form_data = {
        "requested_actions": ["do_something"],
        "backend": backend.slug,
    }
    form = JobRequestCreateForm(
        ["do_something"],
        backends=choices,
        database_actions=[],
        codelists_status="ok",
        data=form_data,
    )

    assert "backend" in form.fields
    assert form.fields["backend"].choices == choices
    assert "requested_actions" in form.fields
    assert form.fields["requested_actions"].choices == [
        ("do_something", "do_something")
    ]

    assert form.is_valid(), (form.errors, form.non_field_errors())


def test_jobrequestcreateform_with_multiple_backends():
    BackendFactory.create_batch(3)

    choices = backends_to_choices(Backend.objects.all())
    assert len(choices) == 3
    form = JobRequestCreateForm(
        ["do_something"], backends=choices, database_actions=[], codelists_status="ok"
    )

    assert "backend" in form.fields
    assert form.fields["backend"].choices == choices
    form_data = {
        "requested_actions": ["do_something"],
        "backend": Backend.objects.first().slug,
    }
    form = JobRequestCreateForm(
        ["do_something"],
        backends=choices,
        database_actions=[],
        codelists_status="ok",
        data=form_data,
    )
    assert form.is_valid(), (form.errors, form.non_field_errors())


@pytest.mark.parametrize(
    "requested_actions,is_valid,error_actions",
    [
        (["do_a_db_thing"], False, ["do_a_db_thing"]),
        (["do_a_non_db_thing"], True, []),
        (
            ["do_a_db_thing", "do_another_db_thing", "do_a_non_db_thing"],
            False,
            ["do_a_db_thing", "do_another_db_thing"],
        ),
    ],
)
def test_jobrequestcreateform_with_bad_codelists(
    requested_actions, is_valid, error_actions
):
    backend = BackendFactory()
    choices = backends_to_choices(Backend.objects.all())
    form_data = {
        "requested_actions": requested_actions,
        "backend": backend.slug,
    }

    form = JobRequestCreateForm(
        ["do_a_db_thing", "do_another_db_thing", "do_a_non_db_thing"],
        backends=choices,
        database_actions=["do_a_db_thing", "do_another_db_thing"],
        codelists_status="error",
        data=form_data,
    )
    assert form.is_valid() == is_valid
    if not is_valid:
        assert len(form.non_field_errors()) == 1
        assert (
            "Some requested actions cannot be run with out-of-date codelists "
            f"({', '.join(error_actions)})" in form.non_field_errors()[0]
        )


def test_workspacecreateform_unbound():
    """
    When the form is instantiated with multiple repos and branches and no data
    then:
        * The form is unbound.
        * The repo choices include (url, name) pairs for each repo.
        * The branch choices include (name, name) pairs for each branch
          in the first repo (the default selection).
        * The repo and branch initial values are set to None.
    """
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch-1a", "test-branch-1b", "test-branch-1c"],
        },
        {
            "name": "test-repo2",
            "url": "http://example.com/derp/test-repo2",
            "branches": ["test-branch-2a", "test-branch-2b", "test-branch-2c"],
        },
    ]
    form = WorkspaceCreateForm(repos_with_branches)

    assert not form.is_bound
    assert form.fields["repo"].choices == [
        ("http://example.com/derp/test-repo", "test-repo"),
        ("http://example.com/derp/test-repo2", "test-repo2"),
    ]
    assert form.fields["branch"].choices == [
        (
            "test-branch-1a",
            "test-branch-1a",
        ),
        (
            "test-branch-1b",
            "test-branch-1b",
        ),
        (
            "test-branch-1c",
            "test-branch-1c",
        ),
    ]
    assert form.fields["repo"].initial is None
    assert form.fields["branch"].initial is None


@pytest.mark.parametrize(
    "name,cleaned_name",
    [
        pytest.param("test", "test", id="lower_case_name"),
        pytest.param("TeSt", "test", id="mixed_case_name"),
    ],
)
def test_workspacecreateform_success(name, cleaned_name):
    """
    When the form is instantiated with multiple repos and branches wth valid
    data selecting the second repo and third branch, then:
        * The form is bound.
        * The repo choices include (url, name) pairs for each repo.
        * The branch choices include (name, name) pairs for each branch
          in the second repo (the one selected in data).
        * The form validates.
        * The data ends up in the cleaned_data.
        * The name field is cleaned by converting to lower case.
    """
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch-1a", "test-branch-1b", "test-branch-1c"],
        },
        {
            "name": "test-repo2",
            "url": "http://example.com/derp/test-repo2",
            "branches": ["test-branch-2a", "test-branch-2b", "test-branch-2c"],
        },
    ]
    data = {
        "name": name,
        "repo": "http://example.com/derp/test-repo2",
        "branch": "test-branch-2c",
        "purpose": "test purpose",
    }

    form = WorkspaceCreateForm(repos_with_branches, data=data)

    assert form.is_bound
    assert form.fields["repo"].choices == [
        ("http://example.com/derp/test-repo", "test-repo"),
        ("http://example.com/derp/test-repo2", "test-repo2"),
    ]
    assert form.fields["branch"].choices == [
        (
            "test-branch-2a",
            "test-branch-2a",
        ),
        (
            "test-branch-2b",
            "test-branch-2b",
        ),
        (
            "test-branch-2c",
            "test-branch-2c",
        ),
    ]
    assert form.is_valid()
    assert form.cleaned_data["name"] == cleaned_name
    assert form.cleaned_data["repo"] == "http://example.com/derp/test-repo2"
    assert form.cleaned_data["branch"] == "test-branch-2c"
    assert form.cleaned_data["purpose"] == "test purpose"


def test_workspacecreateform_unknown_branch_validation_fails():
    """When the form cleaned_data has an unknown branch, validation fails."""
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
        "repo": "http://example.com/derp/test-repo",
        "branch": "unknown-branch",
    }

    with pytest.raises(ValidationError) as e:
        form.clean()

    assert e.value.message.startswith("Unknown branch")


def test_workspacecreateform_unknown_repo_validation_fails():
    """When the form cleaned_data has an unknown repo, validation fails."""
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
        "repo": "unknown-repo",
        "branch": "test-branch",
    }

    with pytest.raises(ValidationError) as e:
        form.clean()

    assert e.value.message.startswith("Unknown repo")


def test_workspacecreateform_duplicate_name_validation_fails():
    """When a Workspace already exists with the chosen name, validation fails."""
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


def test_workspacecreateform_no_repo_match_validation_fails():
    """When form data includes a repo not in the provided set, validation fails."""
    WorkspaceFactory(name="test")

    data = {
        "name": "test",
        "repo": "different",
        "branch": "test",
        "purpose": "test",
    }
    repos_with_branches = [{"name": "test", "url": "test", "branches": ["test"]}]
    with pytest.raises(ValidationError):
        WorkspaceCreateForm(repos_with_branches, data=data)
