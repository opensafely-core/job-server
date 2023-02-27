import pytest
from django.conf import settings

from interactive import Analysis, Codelist
from interactive.submit import (
    AnalysisTemplate,
    clean_working_tree,
    commit_and_push,
    create_commit,
    git,
    raise_if_commit_exists,
    submit_analysis,
)
from jobserver.models.common import new_ulid_str

from ...factories import (
    BackendFactory,
    ProjectFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)
from ...fakes import FakeOpenCodelistsAPI


def commit_in_remote(*, remote, commit):
    ps = git("ls-remote", "--heads", remote, capture_output=True)

    return ps.stdout.startswith(commit)


def tag_in_remote(*, remote, tag):
    ps = git("ls-remote", "--tags", remote, tag, capture_output=True)

    return ps.stdout.endswith(f"{tag}\n")


def tag_points_at_sha(*, repo, tag, sha):
    ps = git("rev-list", "-1", tag, capture_output=True, cwd=repo)

    return ps.stdout == f"{sha}\n"


def test_clean_working_tree(tmp_path):
    one = tmp_path / "1"
    one.mkdir()
    (one / "1").write_text("")
    (one / "2").write_text("")
    (one / "3").write_text("")

    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("")

    (tmp_path / "testing").mkdir()

    clean_working_tree(tmp_path)

    assert not (tmp_path / "1" / "1").exists()
    assert not (tmp_path / "1" / "2").exists()
    assert not (tmp_path / "1" / "3").exists()
    assert not (tmp_path / "testing").exists()
    assert (tmp_path / ".git" / "config").exists()


@pytest.mark.parametrize(
    "codelist_2,commit_message",
    [
        (None, "Codelist slug-a"),
        (
            Codelist(label="", slug="slug-b", system="", type=""),
            "Codelist slug-a and codelist slug-b",
        ),
    ],
    ids=["with_codelist_2", "without_codelist_2"],
)
def test_commit_and_push(build_repo, remote_repo, codelist_2, commit_message):
    # create the git repo which would be tied to a workspace
    repo = build_repo()

    # set our remote_repo fixture as the remote "origin"
    git("remote", "add", "origin", remote_repo, cwd=repo)

    pk = new_ulid_str()

    analysis = Analysis(
        codelist_1=Codelist(label="", slug="slug-a", system="", type=""),
        codelist_2=codelist_2,
        created_by=UserFactory().email,
        demographics="",
        filter_population="",
        repo=repo,
        id=pk,
        time_scale="",
        time_value="",
        title="",
    )

    (repo / "first.txt").write_text("testing")
    sha = commit_and_push(repo, analysis)

    # assert commit is in pushed remote_repo
    assert commit_in_remote(remote=remote_repo, commit=sha)
    assert tag_in_remote(remote=remote_repo, tag=pk)

    # assert tag is for new commit
    assert tag_points_at_sha(repo=repo, tag=pk, sha=sha)

    # commit again with the same analysis to test force tagging
    (repo / "second.txt").write_text("testing")
    sha = commit_and_push(repo, analysis, force=True)

    # assert new commit is in remote repo
    assert commit_in_remote(remote=remote_repo, commit=sha)
    assert tag_in_remote(remote=remote_repo, tag=pk)

    # assert tag has been updated to point to second commit
    assert tag_points_at_sha(repo=repo, tag=pk, sha=sha)


def test_raise_if_commit_exists(tmp_path):
    git("init", ".", "--initial-branch", "main", cwd=tmp_path)

    (tmp_path / "first").write_text("")
    git("add", "first", cwd=tmp_path)
    git(
        "-c",
        "user.email=testing@opensafely.org",
        "-c",
        "user.name=testing",
        "commit",
        "-m",
        "add first",
        cwd=tmp_path,
    )
    git("tag", "exists", cwd=tmp_path)

    with pytest.raises(Exception, match="Commit for exists"):
        raise_if_commit_exists(tmp_path, "exists")

    assert raise_if_commit_exists(tmp_path, "missing") is None


@pytest.mark.parametrize(
    "force", [(True), (False)], ids=["force_commit", "without_force_commit"]
)
def test_create_commit(build_repo, remote_repo, template_repo, force):
    # set our remote_repo fixture as the remote "origin"
    git("remote", "add", "origin", remote_repo, cwd=remote_repo)

    pk = new_ulid_str()

    analysis = Analysis(
        codelist_1=Codelist(label="", slug="", system="", type=""),
        codelist_2=None,
        created_by=UserFactory().email,
        demographics="",
        filter_population="",
        repo=remote_repo,
        id=pk,
        time_scale="",
        time_value="",
        title="",
    )

    sha, project_yaml = create_commit(
        analysis,
        template_repo,
        force=force,
        get_opencodelists_api=FakeOpenCodelistsAPI,
    )

    # does the remote repo only have the files we expect from our template?
    ps = git(
        "ls-tree",
        "--full-tree",
        "--name-only",
        "-r",  # recurse
        "HEAD",
        cwd=remote_repo,
        capture_output=True,
    )
    assert ps.stdout.strip().split("\n") == [
        "analysis/test.py",
        "codelists/codelist_1.csv",
        "project.yaml",
    ]

    assert commit_in_remote(remote=remote_repo, commit=sha)


def test_create_commit_bad_template_repo(build_repo, remote_repo, tmp_path):
    repo = build_repo("template_repo")
    git(
        "-c",
        "user.email=testing@opensafely.org",
        "-c",
        "user.name=testing",
        "commit",
        "--allow-empty",
        "-m",
        "test",
        cwd=repo,
    )
    pk = new_ulid_str()
    analysis = Analysis(
        codelist_1=Codelist(label="", slug="", system="", type=""),
        codelist_2=None,
        created_by=UserFactory().email,
        demographics="",
        filter_population="",
        repo="",
        id=pk,
        time_scale="",
        time_value="",
        title="",
    )

    with pytest.raises(RuntimeError) as e:
        create_commit(
            analysis, repo, force=True, get_opencodelists_api=FakeOpenCodelistsAPI
        )

    assert "does not have a templates/v2 directory" in str(e.value)


@pytest.mark.parametrize(
    "force", [(True), (False)], ids=["force_commit", "without_force_commit"]
)
def test_create_commit_with_two_codelists(
    build_repo, remote_repo, template_repo, force
):
    # set our remote_repo fixture as the remote "origin"
    git("remote", "add", "origin", remote_repo, cwd=remote_repo)

    pk = new_ulid_str()

    analysis = Analysis(
        codelist_1=Codelist(label="", slug="", system="", type=""),
        codelist_2=Codelist(label="", slug="slug-b", system="", type=""),
        created_by=UserFactory().email,
        demographics="",
        filter_population="",
        repo=remote_repo,
        id=pk,
        time_scale="",
        time_value="",
        title="",
    )

    sha, project_yaml = create_commit(
        analysis,
        template_repo,
        force=force,
        get_opencodelists_api=FakeOpenCodelistsAPI,
    )

    # does the remote repo only have the files we expect from our template?
    ps = git(
        "ls-tree",
        "--full-tree",
        "--name-only",
        "-r",  # recurse
        "HEAD",
        cwd=remote_repo,
        capture_output=True,
    )
    assert ps.stdout.strip().split("\n") == [
        "analysis/test.py",
        "codelists/codelist_1.csv",
        "codelists/codelist_2.csv",
        "project.yaml",
    ]

    assert commit_in_remote(remote=remote_repo, commit=sha)


def test_submit_analysis(monkeypatch, remote_repo, template_repo):
    monkeypatch.setattr(settings, "INTERACTIVE_TEMPLATE_REPO", str(template_repo))

    backend = BackendFactory()
    project = ProjectFactory()
    repo = RepoFactory(url=str(remote_repo))
    WorkspaceFactory(project=project, repo=repo, name=f"{project.slug}-interactive")
    user = UserFactory()

    analysis = Analysis(
        codelist_1=Codelist(label="", slug="slug-a", system="", type=""),
        codelist_2=None,
        created_by=user.email,
        demographics="",
        filter_population="",
        repo=str(remote_repo),
        time_scale="",
        time_value="",
        title="test",
    )

    analysis_request = submit_analysis(
        analysis=analysis,
        backend=backend,
        creator=user,
        project=project,
        get_opencodelists_api=FakeOpenCodelistsAPI,
    )

    assert analysis_request.created_by == user
    assert analysis_request.job_request
    assert analysis_request.project == project
    assert analysis_request.template_data["codelist_1"]["slug"] == "slug-a"
    assert analysis_request.title == "test"


def test_interactive_analysis_template_success(template_repo, tmp_path):

    template_dir = template_repo / "templates/v2"
    template = AnalysisTemplate(template_dir, [], FakeOpenCodelistsAPI)
    template.render(tmp_path, {})

    assert (tmp_path / "project.yaml").read_text() == "test: test"
    assert (tmp_path / "analysis/test.py").read_text() == "print('test')"


def test_interactive_analysis_template_skips_files(template_repo, tmp_path):

    template_dir = template_repo / "templates/v2"
    (template_dir / "__pycache__").mkdir()
    template = AnalysisTemplate(template_dir, [], FakeOpenCodelistsAPI)
    template.render(tmp_path, {})

    assert (tmp_path / "project.yaml").exists() is True
    assert (tmp_path / "__pycache__").exists() is False
