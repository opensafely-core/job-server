from jobserver.models import Backend, Project
from jobserver.utils import set_from_qs
from staff.forms import (
    ApplicationApproveForm,
    ProjectCreateForm,
    ProjectEditForm,
    ProjectLinkApplicationForm,
    UserCreateForm,
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
        {
            "project_name": "test project",
            "project_number": "42",
            "org": str(org.pk),
        }
    )

    assert form.is_valid(), form.errors


def test_applicationapproveform_with_duplicate_project_name():
    org = OrgFactory()
    project = ProjectFactory()

    form = ApplicationApproveForm(
        {
            "project_name": project.name,
            "project_number": "42",
            "org": str(org.pk),
        }
    )

    assert not form.is_valid()
    assert form.errors == {
        "project_name": [f'Project "{project.name}" already exists.']
    }


def test_applicationapproveform_with_duplicate_project_number():
    org = OrgFactory()
    project = ProjectFactory(number=42)

    form = ApplicationApproveForm(
        {
            "project_name": "test",
            "project_number": "42",
            "org": str(org.pk),
        }
    )

    assert not form.is_valid()
    assert form.errors == {
        "project_number": [f'Project with number "{project.number}" already exists.']
    }


def test_applicationapproveform_with_duplicate_project_slug():
    org = OrgFactory()
    ProjectFactory(slug="test-1")

    form = ApplicationApproveForm(
        {
            "project_name": "Test 1",
            "project_number": "42",
            "org": str(org.pk),
        }
    )

    assert not form.is_valid()
    assert form.errors == {
        "project_name": ['A project with the slug, "test-1", already exists']
    }


def test_applicationapproveform_with_empty_project_slug():
    org = OrgFactory()

    form = ApplicationApproveForm(
        {
            "project_name": "-/-.",
            "project_number": "42",
            "org": str(org.pk),
        }
    )

    assert not form.is_valid()
    assert form.errors == {
        "project_name": ["Please use at least one letter or number in the title"]
    }


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
        "org": str(org.pk),
        "status": Project.Statuses.RETIRED,
    }

    form = ProjectEditForm(data=data)
    assert form.is_valid(), form.errors

    form = ProjectEditForm(data=data | {"number": 123})
    assert form.is_valid(), form.errors


def test_projectcreateform_with_duplicate_number():
    copilot = UserFactory()
    org = OrgFactory()
    project = ProjectFactory(number=42)

    data = {
        "org": str(org.pk),
        "copilot": str(copilot.pk),
        "application_url": "http://example.com",
        "name": "Test",
        "number": project.number,
    }
    form = ProjectCreateForm(data=data)

    assert not form.is_valid()

    assert form.errors == {"number": ["Project number must be unique"]}


def test_projecteditform_with_duplicate_number():
    project = ProjectFactory()
    other_project = ProjectFactory(number=42)

    data = {
        "name": project.name,
        "slug": project.slug,
        "number": other_project.number,
        "org": str(project.org.pk),
        "status": project.status,
    }
    form = ProjectEditForm(data=data, instance=project)

    assert not form.is_valid()

    assert form.errors == {"number": ["Project number must be unique"]}


def test_projecteditform_with_existing_number():
    project = ProjectFactory(number=42)

    data = {
        "name": project.name,
        "slug": project.slug,
        "number": project.number,
        "org": str(project.org.pk),
        "status": project.status,
    }
    form = ProjectEditForm(data=data, instance=project)

    assert form.is_valid(), form.errors


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


def test_usercreateform_without_project():
    data = {
        "name": "test",
        "email": "test@example.com",
    }
    form = UserCreateForm(data=data)

    # we depend on project in UserCreateForm.clean so confirm the form can
    # still be validated without throwing an exception when it's missing
    assert not form.is_valid()


def test_userform_success():
    backend1 = BackendFactory()
    backend2 = BackendFactory()
    BackendFactory()

    data = {
        "backends": [backend1.slug, backend2.slug],
    }
    form = UserForm(
        available_backends=Backend.objects.all(),
        data=data,
        fullname="",
    )

    assert form.is_valid(), form.errors

    assert set_from_qs(form.cleaned_data["backends"]) == {backend1.pk, backend2.pk}


def test_userform_with_no_backends():
    available_backends = Backend.objects.filter(slug__in=["tpp"])

    form = UserForm(
        available_backends=available_backends,
        data={"backends": []},
        fullname="",
    )

    assert form.is_valid()
    assert len(form.cleaned_data["backends"]) == 0


def test_userform_with_unknown_backend():
    BackendFactory.create_batch(5)

    available_backends = Backend.objects.exclude(slug="unknown")

    form = UserForm(
        available_backends=available_backends,
        data={"backends": ["unknown"]},
        fullname="",
    )

    assert not form.is_valid()
    assert form.errors == {
        "backends": [
            "Select a valid choice. unknown is not one of the available choices."
        ]
    }
