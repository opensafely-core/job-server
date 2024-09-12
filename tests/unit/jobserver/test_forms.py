import pytest
from django.core.exceptions import ValidationError

from jobserver.backends import backends_to_choices
from jobserver.forms import JobRequestCreateForm, WorkspaceCreateForm
from jobserver.models import Backend

from ...factories import BackendFactory, ProjectFactory, WorkspaceFactory


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


def test_workspacecreateform_success():
    project = ProjectFactory()
    data = {
        "name": "test",
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


def test_workspacecreateform_with_no_repo_match():
    project = ProjectFactory()
    WorkspaceFactory(name="test")

    data = {
        "name": "test",
        "repo": "different",
        "branch": "test",
        "purpose": "test",
    }
    repos_with_branches = [{"name": "test", "url": "test", "branches": ["test"]}]
    with pytest.raises(ValidationError):
        WorkspaceCreateForm(project, repos_with_branches, data=data)
