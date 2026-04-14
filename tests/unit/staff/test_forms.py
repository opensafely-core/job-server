import pytest

from jobserver.models import Backend, Project
from jobserver.utils import set_from_qs
from staff.forms import (
    ApplicationApproveForm,
    ProjectCreateForm,
    ProjectEditForm,
    ProjectLinkApplicationForm,
    UserForm,
    WorkspaceEditForm,
)

from ...factories import (
    ApplicationFactory,
    BackendFactory,
    CreateProjectFormDataFactory,
    OrgFactory,
    ProjectFactory,
    UserFactory,
)


def test_applicationapproveform_success():
    org = OrgFactory(slug="test-org")

    form = ApplicationApproveForm(
        data={
            "project_name": "test project",
            "project_number": "42",
            "org": str(org.pk),
        },
        orgs=[org],
    )

    assert form.is_valid(), form.errors


def test_applicationapproveform_with_duplicate_project_name():
    org = OrgFactory()
    project = ProjectFactory()

    form = ApplicationApproveForm(
        data={
            "project_name": project.name,
            "project_number": "42",
            "org": str(org.pk),
        },
        orgs=[org],
    )

    assert not form.is_valid()
    assert "project_name" in form.errors


def test_applicationapproveform_with_duplicate_project_number():
    org = OrgFactory()
    ProjectFactory(number=42)

    form = ApplicationApproveForm(
        data={
            "project_name": "test",
            "project_number": "42",
            "org": str(org.pk),
        },
        orgs=[org],
    )

    assert not form.is_valid()
    assert "project_number" in form.errors


def test_applicationapproveform_with_duplicate_project_slug():
    org = OrgFactory()
    ProjectFactory(slug="test-1")

    form = ApplicationApproveForm(
        data={
            "project_name": "Test 1",
            "project_number": "42",
            "org": str(org.pk),
        },
        orgs=[org],
    )

    assert not form.is_valid()
    assert "project_name" in form.errors


def test_applicationapproveform_with_empty_project_slug():
    org = OrgFactory()

    form = ApplicationApproveForm(
        data={
            "project_name": "-/-.",
            "project_number": "42",
            "org": str(org.pk),
        },
        orgs=[org],
    )

    assert not form.is_valid()
    assert "project_name" in form.errors


def test_applicationapproveform_with_alphanumeric_project_number():
    org = OrgFactory()

    form = ApplicationApproveForm(
        data={
            "project_name": "test",
            "project_number": "POS-2025-2001",
            "org": str(org.pk),
        },
        orgs=[org],
    )

    assert form.is_valid(), form.errors


def test_applicationapproveform_with_invalid_project_number():
    org = OrgFactory()

    form = ApplicationApproveForm(
        data={
            "project_name": "test",
            "project_number": "POS-invalid-format",
            "org": str(org.pk),
        },
        orgs=[org],
    )

    assert not form.is_valid()
    assert "project_number" in form.errors


def test_applicationapproveform_rejects_leading_zero_numeric_project_number():
    org = OrgFactory()

    form = ApplicationApproveForm(
        data={
            "project_name": "test",
            "project_number": "00126",
            "org": str(org.pk),
        },
        orgs=[org],
    )

    assert not form.is_valid()
    assert "project_number" in form.errors


def test_projectcreateform_unbound(potential_copilots):
    """
    Test unbound state for ProjectCreate form.

    When the form is instantiated then:
        * The form is unbound.
        * name and number fields do not have initial values.
        * The copilot field has the expected queryset.
    """

    form = ProjectCreateForm()

    assert not form.is_bound
    assert form.fields["name"].initial is None
    assert form.fields["number"].initial is None
    assert set(form.fields["copilot"].queryset) == set(potential_copilots)


def test_projectcreateform_success(potential_copilots):
    """
    Test is_valid() success for ProjectCreate form.

    When the form is populated by the user and submitted then:
        * The form is bound with copilot, orgs, name, and number data input by the user.
        * Validation succeeds.
    """

    data = CreateProjectFormDataFactory(copilot=potential_copilots.first())

    form = ProjectCreateForm(data=data)

    assert form.is_bound
    assert form.is_valid(), form.errors


def test_projectcreateform_duplicate_slug():
    """Test that ProjectCreateForm does not validate when an already existing
    slug would be generated.

    Given a project exists with a particular slug.
    When the form is populated with a name that slugifies to the same thing:
        * Validation fails.
    """
    ProjectFactory(slug="foo")
    data = CreateProjectFormDataFactory()
    data["name"] = "foo"

    form = ProjectCreateForm(data=data)

    assert form.is_bound
    assert not form.is_valid()
    assert "name" in form.errors


def test_projectcreateform_empty_slug():
    """Test that ProjectCreateForm does not validate when an empty
    slug would be generated.

    When the form is populated with a name that slugifies to '':
        * Validation fails.

    This can occur when the name contains only special characters.
    """
    data = CreateProjectFormDataFactory()
    data["name"] = "!!!"

    form = ProjectCreateForm(data=data)

    assert form.is_bound
    assert not form.is_valid()
    assert "name" in form.errors


@pytest.mark.parametrize(
    "invalid_data_type,invalid_data,field",
    [
        ("duplicate_name", {}, "name"),
        ("unknown_org", {"orgs": ["99999"]}, "orgs"),
        ("unknown_copilot", {"copilot": "99999"}, "copilot"),
    ],
)
def test_projectcreateform_invalid_data(
    invalid_data_type, invalid_data, field, potential_copilots
):
    """
    Test invalid data submission to ProjectCreateForm

    Parametrised invalid data: duplicate project name, an unknown organisation, and an unknown copilot user.

    When invalid data are submitted:
    - is_valid() fails
    - we get a form error for the expected field
    """

    existing_project = ProjectFactory()

    valid_data = CreateProjectFormDataFactory(copilot=potential_copilots.first())
    invalid_data = valid_data | invalid_data

    if invalid_data_type == "duplicate_name":
        invalid_data["name"] = existing_project.name

    form = ProjectCreateForm(data=invalid_data)
    assert not form.is_valid()
    assert field in form.errors


@pytest.mark.parametrize("field", ["name", "orgs", "copilot"])
@pytest.mark.parametrize("missing_type", ["empty", "omitted"])
@pytest.mark.parametrize("project_number", ["123", "POS-2026-2001"])
def test_projectcreateform_without_required_data(
    field, missing_type, project_number, potential_copilots
):
    """
    Test submission of empty and omitted values for each required field in the ProjectCreateForm.

    When empty or omitted values are submitted:
    - is_valid() is False
    - we get a form error for the expected field
    Except if the missing field is copilot and the project number is not such
    that the copilot field is required. In that case:
    - is_valid() is True
    """
    data = CreateProjectFormDataFactory(
        number=project_number, copilot=potential_copilots.first()
    )

    if missing_type == "empty":
        if field == "orgs":
            data[field] = []
        else:
            data[field] = ""
    else:
        data.pop(field, None)

    form = ProjectCreateForm(data=data)

    # Copilot is only required for POS- projects.
    if project_number == "123" and field == "copilot":
        assert form.is_valid()
    else:
        assert not form.is_valid()
        assert set(form.errors.keys()) == {field}
        assert len(form.errors[field]) == 1
        assert "is required" in form.errors[field][0]


def test_projecteditform_unbound(potential_copilots):
    """
    Test unbound state for ProjectEditForm.

    When the form is instantiated then:
        * The form is unbound.
        * The copilot field has the expected queryset.
    """

    form = ProjectEditForm()

    assert not form.is_bound
    assert set(form.fields["copilot"].queryset) == set(potential_copilots)


def test_projecteditform_number_is_not_required():
    """
    Ensure Project.number isn't required by ProjectEditForm

    Project.number is nullable while we get all project data ported into this
    project.
    """
    org = OrgFactory()

    data = {
        "name": "Test",
        "slug": "test",
        "orgs": [str(org.pk)],
        "status": Project.Statuses.RETIRED,
    }

    form = ProjectEditForm(data=data)
    assert form.is_valid(), form.errors

    form = ProjectEditForm(data=data | {"number": 123})
    assert form.is_valid(), form.errors


def test_projecteditform_with_duplicate_number():
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])

    other_project = ProjectFactory(number=42)

    data = {
        "name": project.name,
        "slug": project.slug,
        "number": other_project.number,
        "orgs": [str(org.pk)],
        "status": project.status,
    }
    form = ProjectEditForm(data=data, instance=project)

    assert not form.is_valid()

    assert form.errors == {"number": ["Project with this Project ID already exists."]}


def test_projecteditform_rejects_leading_zero_numeric_project_number():
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])

    data = {
        "name": project.name,
        "slug": project.slug,
        "number": "0042",
        "orgs": [str(org.pk)],
        "status": project.status,
    }
    form = ProjectEditForm(data=data, instance=project)

    assert not form.is_valid()
    assert form.errors == {
        "number": [
            "Enter a whole number or use the format POS-20YY-NNNN (for example, POS-2026-2001)."
        ]
    }


def test_projecteditform_with_existing_number():
    org = OrgFactory()
    project = ProjectFactory(number=42, orgs=[org])

    data = {
        "name": project.name,
        "slug": project.slug,
        "number": project.number,
        "orgs": [str(org.pk)],
        "status": project.status,
    }
    form = ProjectEditForm(data=data, instance=project)

    assert form.is_valid(), form.errors


def test_projecteditform_rejects_invalid_alphanumeric_number():
    org = OrgFactory()
    project = ProjectFactory(number=42, orgs=[org])

    data = {
        "name": project.name,
        "slug": project.slug,
        "number": "POS-invalid-format",
        "orgs": [str(org.pk)],
        "status": project.status,
    }
    form = ProjectEditForm(data=data, instance=project)

    assert not form.is_valid()
    assert form.errors == {
        "number": [
            "Enter a whole number or use the format POS-20YY-NNNN (for example, POS-2026-2001)."
        ]
    }


@pytest.mark.parametrize(
    "existing_number, new_number",
    [
        (None, "42"),
        (None, "POS-2025-2001"),
        ("42", None),
        ("42", "POS-2025-2001"),
        ("POS-2025-2001", None),
        ("POS-2025-2001", "42"),
    ],
)
def test_projecteditform_cleans_number_transitions(existing_number, new_number):
    org = OrgFactory()
    project = ProjectFactory(number=existing_number, orgs=[org])

    data = {
        "name": project.name,
        "slug": project.slug,
        "number": new_number,
        "orgs": [str(org.pk)],
        "status": project.status,
    }
    form = ProjectEditForm(data=data, instance=project)
    print("existing_number:", existing_number)
    print("new_number:", new_number)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["number"] == new_number


def test_projectlinkapplicationform_success():
    application = ApplicationFactory(project=None)

    form = ProjectLinkApplicationForm(
        data={"application": application.pk}, instance=None
    )
    assert form.is_valid(), form.errors

    assert form.cleaned_data["application"] == application


def test_projectlinkapplicationform_with_already_linked_application():
    application = ApplicationFactory(project=ProjectFactory())

    form = ProjectLinkApplicationForm(
        data={"application": application.pk}, instance=None
    )

    assert not form.is_valid()

    assert form.errors == {
        "application": ["Can't link Application to multiple Projects"]
    }


def test_projectlinkapplicationform_with_unknown_application():
    form = ProjectLinkApplicationForm(data={"application": "0"}, instance=None)

    assert not form.is_valid()

    assert form.errors == {"application": ["Unknown Application"]}


def test_userform_success():
    backend1 = BackendFactory()
    backend2 = BackendFactory()
    BackendFactory()
    user = UserFactory()

    data = {
        "backends": [backend1.slug, backend2.slug],
    }
    form = UserForm(
        available_backends=Backend.objects.all(),
        data=data,
        fullname=user.fullname,
    )

    assert form.is_valid(), form.errors

    assert set_from_qs(form.cleaned_data["backends"]) == {backend1.pk, backend2.pk}


def test_userform_with_no_backends():
    user = UserFactory()
    available_backends = Backend.objects.filter(slug__in=["tpp"])

    form = UserForm(
        available_backends=available_backends,
        data={"backends": []},
        fullname=user.fullname,
    )

    assert form.is_valid()
    assert len(form.cleaned_data["backends"]) == 0


def test_userform_with_unknown_backend():
    BackendFactory.create_batch(5)
    user = UserFactory()

    available_backends = Backend.objects.exclude(slug="unknown")

    form = UserForm(
        available_backends=available_backends,
        data={"backends": ["unknown"]},
        fullname=user.fullname,
    )

    assert not form.is_valid()
    assert form.errors == {
        "backends": [
            "Select a valid choice. unknown is not one of the available choices."
        ]
    }


def test_workspaceeditform_projects_are_ordered_by_project_number(
    project_ordering_rows,
):
    project_rows, expected_order = project_ordering_rows
    created_projects = {
        row.name: ProjectFactory(name=row.name, number=row.number)
        for row in project_rows
    }

    form = WorkspaceEditForm()

    ordered_project_ids = list(
        form.fields["project"].queryset.values_list("pk", flat=True)
    )

    assert ordered_project_ids == [created_projects[name].pk for name in expected_order]
