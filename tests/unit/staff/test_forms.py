from jobserver.models import Backend, Project
from jobserver.utils import set_from_qs
from staff.forms import (
    ApplicationApproveForm,
    ProjectCreateForm,
    ProjectEditForm,
    ProjectLinkApplicationForm,
    UserForm,
)

from ...factories import (
    ApplicationFactory,
    BackendFactory,
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
    assert form.errors == {
        "project_name": [f'Project "{project.name}" already exists.']
    }


def test_applicationapproveform_with_duplicate_project_number():
    org = OrgFactory()
    project = ProjectFactory(number=42)

    form = ApplicationApproveForm(
        data={
            "project_name": "test",
            "project_number": "42",
            "org": str(org.pk),
        },
        orgs=[org],
    )

    assert not form.is_valid()
    assert form.errors == {
        "project_number": [f'Project with number "{project.number}" already exists.']
    }


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
    assert form.errors == {
        "project_name": ['A project with the slug, "test-1", already exists']
    }


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
    assert form.errors == {
        "project_name": ["Please use at least one letter or number in the title"]
    }


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
    assert form.errors == {
        "project_number": [
            "Enter a numeric project number or one in the format POS-20YY-NNNN (for example, POS-2025-2001)."
        ]
    }


def test_applicationapproveform_rejects_duplicate_number_after_normalisation():
    org = OrgFactory()
    ProjectFactory(number="126")

    form = ApplicationApproveForm(
        data={
            "project_name": "test",
            "project_number": "00126",
            "org": str(org.pk),
        },
        orgs=[org],
    )

    assert not form.is_valid()
    assert form.errors == {
        "project_number": ['Project with number "126" already exists.']
    }


def test_projectcreateform_unbound():
    """
    Test unbound state for ProjectCreate form.

    When the form is instantiated then:
        * The form is unbound.
        * name and number fields do not have initial values.
    """

    form = ProjectCreateForm()

    assert not form.is_bound
    assert form.fields["name"].initial is None
    assert form.fields["number"].initial is None


def test_projectcreateform_success():
    """
    Test is_valid() success for ProjectCreate form.

    When the form is populated by the user and submitted then:
        * The form is bound with copilot, orgs, name, and number data input by the user.
        * Validation succeeds.
    """
    copilot = UserFactory()
    org = OrgFactory()

    data = {
        "name": "test1",
        "number": 1234567832,
        "orgs": [str(org.pk)],
        "copilot": str(copilot.pk),
    }

    form = ProjectCreateForm(data=data)

    assert form.is_bound
    assert form.is_valid(), form.errors


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

    assert form.errors == {"number": ["Project number must be unique"]}


def test_projecteditform_rejects_duplicate_number_after_normalisation():
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])
    ProjectFactory(number="42")

    data = {
        "name": project.name,
        "slug": project.slug,
        "number": "0042",
        "orgs": [str(org.pk)],
        "status": project.status,
    }
    form = ProjectEditForm(data=data, instance=project)

    assert not form.is_valid()

    assert form.errors == {"number": ["Project number must be unique"]}


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


def test_projecteditform_allows_changing_numeric_number_to_alphanumeric():
    org = OrgFactory()
    project = ProjectFactory(number=42, orgs=[org])

    data = {
        "name": project.name,
        "slug": project.slug,
        "number": "POS-2025-2001",
        "orgs": [str(org.pk)],
        "status": project.status,
    }
    form = ProjectEditForm(data=data, instance=project)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["number"] == "POS-2025-2001"


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
            "Enter a numeric project number or one in the format POS-20YY-NNNN (for example, POS-2025-2001)."
        ]
    }


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
