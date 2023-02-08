import pytest
from django.conf import settings

from interactive import Analysis, Codelist
from interactive.submit import (
    clean_working_tree,
    commit_and_push,
    create_commit,
    download_codelist,
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
            Codelist(label="", slug="slug-b", type=""),
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
        codelist_1=Codelist(
            label="",
            slug="slug-a",
            type="",
        ),
        codelist_2=codelist_2,
        created_by=UserFactory().email,
        demographics="",
        filter_population="",
        frequency="",
        repo=repo,
        identifier=pk,
        time_event="",
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


def test_download_codelist(tmp_path):
    path = tmp_path / "codlist.csv"
    download_codelist("test", path, get_opencodelists_api=FakeOpenCodelistsAPI)
    assert path.exists()


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
        codelist_1=Codelist(label="", slug="", type=""),
        codelist_2=None,
        created_by=UserFactory().email,
        demographics="",
        filter_population="",
        frequency="",
        repo=remote_repo,
        identifier=pk,
        time_event="",
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
        "HEAD",
        cwd=remote_repo,
        capture_output=True,
    )
    assert ps.stdout == "codelist_1.csv\nproject.yaml\n"

    assert commit_in_remote(remote=remote_repo, commit=sha)


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
        codelist_1=Codelist(label="", slug="", type=""),
        codelist_2=Codelist(label="", slug="slug-b", type=""),
        created_by=UserFactory().email,
        demographics="",
        filter_population="",
        frequency="",
        repo=remote_repo,
        identifier=pk,
        time_event="",
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
        "HEAD",
        cwd=remote_repo,
        capture_output=True,
    )
    assert ps.stdout == "codelist_1.csv\ncodelist_2.csv\nproject.yaml\n"

    assert commit_in_remote(remote=remote_repo, commit=sha)


def test_submit_analysis(monkeypatch, remote_repo, template_repo):
    monkeypatch.setattr(settings, "INTERACTIVE_TEMPLATE_REPO", str(template_repo))

    backend = BackendFactory()
    project = ProjectFactory()
    repo = RepoFactory(url=str(remote_repo))
    WorkspaceFactory(project=project, repo=repo, name=f"{project.slug}-interactive")
    user = UserFactory()

    analysis = Analysis(
        codelist_1=Codelist(label="", slug="slug-a", type=""),
        codelist_2=None,
        created_by=user.email,
        demographics="",
        filter_population="",
        frequency="",
        repo=str(remote_repo),
        time_event="",
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
