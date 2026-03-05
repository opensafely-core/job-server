import importlib
import pkgutil
import re

import pytest

from jobserver import permissions
from jobserver.permissions.validator import validate_project_identifier_in_permissions


PERMISSIONS_VARIABLE_NAME_PATTERN = re.compile(r"^PROJECTS_WITH_[A-Z0-9_]+_PERMISSION$")


def collect_project_permission_vars():
    """Find the variables corresponding to project permissions.

    It is assumed that those variables are top-level in the module
    with a name corresponding to the PERMISSIONS_VARIABLE_NAME_PATTERN"""
    package = permissions
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        module = importlib.import_module(module_name)

        for name, value in vars(module).items():
            if PERMISSIONS_VARIABLE_NAME_PATTERN.match(name):
                yield module_name, name, value


_test_project_permission_vars_params = list(collect_project_permission_vars())


@pytest.mark.parametrize(
    "module_name,var_name,value",
    _test_project_permission_vars_params,
    ids=[f"{m}::{n}" for m, n, _ in _test_project_permission_vars_params],
)
def test_project_permission_vars(module_name, var_name, value):
    validate_project_identifier_in_permissions(value)
