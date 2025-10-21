"""Tests of the literal repository content."""

import pytest
import yaml


@pytest.mark.slow_test
def test_development_db_version_is_consistent(request):
    """This test is to ensure that the separately configured database service
    in the GitHub Actions test workflow is consistent with the Docker Compose
    configuration provided for local development.

    When updating the database version, update it in both of those configurations,
    and in this test."""
    root_path = request.config.rootpath

    ci_workflow_path = root_path / ".github" / "workflows" / "main.yml"
    with ci_workflow_path.open() as f:
        ci_yaml = yaml.safe_load(f)
        ci_postgres_version = ci_yaml["jobs"]["test"]["services"]["postgres"]["image"]

    docker_compose_path = root_path / "docker" / "docker-compose.yaml"
    with docker_compose_path.open() as f:
        docker_yaml = yaml.safe_load(f)
        docker_postgres_version = docker_yaml["services"]["db"]["image"]

    assert ci_postgres_version == docker_postgres_version == "postgres:17"
