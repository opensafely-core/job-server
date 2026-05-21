import importlib
import pkgutil

import pytest

from jobserver import permissions


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(
            permissions.dataset_permissions.datasets.PROJECTS_WITH_PERMISSION,
            id="PROJECTS_WITH_PERMISSION",
        ),
        pytest.param(
            permissions.population_permissions.gp_activations.PROJECTS_WITH_GP_ACTIVATIONS_PERMISSION,
            id="PROJECTS_WITH_GP_ACTIVATIONS_PERMISSION",
        ),
        pytest.param(
            permissions.population_permissions.ndoo.PROJECTS_WITH_NDOO_PERMISSION,
            id="PROJECTS_WITH_NDOO_PERMISSION",
        ),
        pytest.param(
            permissions.population_permissions.t1oo.PROJECTS_WITH_T1OO_PERMISSION,
            id="PROJECTS_WITH_T1OO_PERMISSION",
        ),
    ],
)
def test_project_permission_vars(value):
    permissions.validator.validate_project_identifier_in_permissions(value)


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
