from jobserver.models import Backend
from jobserver.utils import set_from_qs
from staff.forms import ApplicationApproveForm, UserForm

from ...factories import BackendFactory, OrgFactory, ProjectFactory


def test_applicationapproveform_success():
    org = OrgFactory(slug="test-org")

    form = ApplicationApproveForm({"project_name": "test project", "org": str(org.pk)})

    assert form.is_valid(), form.errors


def test_applicationapproveform_with_duplicate_project_name():
    org = OrgFactory()
    project = ProjectFactory()

    form = ApplicationApproveForm({"project_name": project.name, "org": str(org.pk)})

    assert not form.is_valid()
    assert form.errors == {
        "project_name": [f'Project "{project.name}" already exists.']
    }


def test_userform_success():
    backend1 = BackendFactory()
    backend2 = BackendFactory()
    BackendFactory()

    data = {
        "backends": [backend1.slug, backend2.slug],
        "is_superuser": ["on"],
        "roles": [],
    }
    form = UserForm(
        available_backends=Backend.objects.all(),
        available_roles=[],
        data=data,
    )

    assert form.is_valid(), form.errors

    assert set_from_qs(form.cleaned_data["backends"]) == {backend1.pk, backend2.pk}

    assert form.cleaned_data["is_superuser"]


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


def test_userform_with_unknown_backend():
    BackendFactory.create_batch(5)

    available_backends = Backend.objects.exclude(slug="unknown")

    data = {
        "backends": ["unknown"],
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
