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
            permissions.t1oo.PROJECTS_WITH_T1OO_PERMISSION,
            id="PROJECTS_WITH_T1OO_PERMISSION",
        ),
    ],
)
def test_project_permission_vars(value):
    permissions.validator.validate_project_identifier_in_permissions(value)
