import pytest
from interactive_templates.fixtures import add_codelist, remote_repo  # noqa

from ...factories import RepoFactory


@pytest.fixture
def interactive_repo(remote_repo):  # noqa ruff bug?
    return RepoFactory(url=str(remote_repo))
