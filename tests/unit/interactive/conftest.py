import pytest
import responses
from interactive_templates.render import CODELIST_URL

from interactive.submit import git

from ...factories import RepoFactory


@pytest.fixture
def build_repo(tmp_path):
    def func(suffix="interactive_repo"):
        path = tmp_path / suffix
        path.mkdir()

        git("init", ".", "--initial-branch", "main", cwd=path)

        return path

    return func


@pytest.fixture
def interactive_repo(remote_repo):
    return RepoFactory(url=str(remote_repo))


@pytest.fixture
def remote_repo(tmp_path):
    path = tmp_path / "remote_repo"
    path.mkdir()

    git("init", "--bare", ".", "--initial-branch", "main", cwd=path)

    return path


@pytest.fixture
def add_codelist():
    with responses.RequestsMock() as rmock:

        def add(slug, contents="code,name\na,aaa\nb,bbb"):
            rmock.get(CODELIST_URL.format(slug, body=contents))

        yield add
