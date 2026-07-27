import importlib
import pkgutil

import pytest

from jobserver import permissions
from jobserver.models import Project


@pytest.mark.parametrize(
    "project_identifiers,variable_name",
    [
        pytest.param(
            permissions.dataset_permissions.datasets.PROJECTS_WITH_PERMISSION,
            "PROJECTS_WITH_PERMISSION",
            id="datasets",
        ),
        pytest.param(
            permissions.population_permissions.gp_activations.PROJECTS_WITH_GP_ACTIVATIONS_PERMISSION,
            "PROJECTS_WITH_GP_ACTIVATIONS_PERMISSION",
            id="gp_activations",
        ),
        pytest.param(
            permissions.population_permissions.ndoo.PROJECTS_WITH_NDOO_PERMISSION,
            "PROJECTS_WITH_GP_ACTIVATIONS_PERMISSION",
            id="ndoo",
        ),
        pytest.param(
            permissions.population_permissions.t1oo.PROJECTS_WITH_T1OO_PERMISSION,
            "PROJECTS_WITH_GP_ACTIVATIONS_PERMISSION",
            id="t1oo",
        ),
    ],
)
def test_project_permission_vars(project_identifiers, variable_name):
    """Test that every project identifier string in every permissions variable is valid.

    Existence of the project in production is not tested. In the datasets test,
    only the keys are examined, not the permission values."""
    for project_identifier in project_identifiers:
        assert (
            Project.is_valid_identifier(project_identifier)
            # This is a specific exemption for the one case where a project slug is used.
            # We should remove this in future and use a standard identifier.
            or project_identifier == "opensafely-internal"
        ), (
            f"Invalid project identifier {project_identifier} used in {variable_name} variable"
        )


def test_all_permission_modules_in_all():
    # Prevent accidentally omitting a new permissions module from its subpackage's __all__
    missing = {}
    for _, subpkg_name, is_pkg in pkgutil.iter_modules(permissions.__path__):
        if not is_pkg:
            continue
        subpkg = importlib.import_module(f"jobserver.permissions.{subpkg_name}")
        subpkg_all = set(getattr(subpkg, "__all__", []))
        for _, mod_name, _ in pkgutil.iter_modules(subpkg.__path__):
            if mod_name not in subpkg_all:  # pragma: no cover
                missing.setdefault(subpkg_name, []).append(mod_name)

    assert not missing, (
        "Missing from __all__ in permissions module's __init__.py:\n"
        + "\n".join(
            f"  permissions.{subpkg_name}: {', '.join(mods)}"
            for subpkg_name, mods in missing.items()
        )
    )
