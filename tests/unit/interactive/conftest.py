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

    template_dir = path / "templates/v2"
    template_dir.mkdir(parents=True)

    (template_dir / "project.yaml.tmpl").write_text("test: {{ 'test' }}")
    (template_dir / "analysis").mkdir()
    (template_dir / "analysis/test.py").write_text("print('test')")

    git("add", ".", cwd=path)
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
