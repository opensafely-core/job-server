import pytest

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
def template_repo(build_repo):
    """Create a repo to match our analysis code template repo"""
    path = build_repo("template_repo")

    (path / "project.yaml").write_text("test content")

    git("add", "project.yaml", cwd=path)
    git(
        "-c",
        "user.email=testing@opensafely.org",
        "-c",
        "user.name=testing",
        "commit",
        "-m",
        "Initial commit",
        cwd=path,
    )

    return path


@pytest.fixture
def remote_repo(tmp_path):
    path = tmp_path / "remote_repo"
    path.mkdir()

    git("init", "--bare", ".", "--initial-branch", "main", cwd=path)

    return path
