import copy
import os
import shutil
import subprocess
import sys
import tempfile
import typing
from pathlib import Path

from attrs import asdict, define
from django.conf import settings
from django.db import transaction
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .models import AnalysisRequest
from .opencodelists import _get_opencodelists_api


# from jobserver.github import create_issue
# from .emails import send_analysis_request_confirmation_email
# from .slacks import notify_analysis_request_submitted


@define
class AnalysisTemplate:
    """Handle rendering teh templated analysis code.

    - directory: the dir containing the source template files
    - codelists: the keys in form_data of any codelists that will need fetchin
                 as part of the rendering
    """

    directory: Path
    codelist_keys: list
    codelist_api: typing.Callable

    EXCLUDES = ["__pycache__", "metadata"]

    @property
    def environment(self):
        return Environment(
            loader=FileSystemLoader(str(self.directory)), undefined=StrictUndefined
        )

    def write_codelist(self, output_dir, key, slug):
        path = output_dir / "codelists" / f"{key}.csv"

        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        api = self.codelist_api()
        codelist = api.get_codelist(slug)
        path.write_text(codelist)
        return path

    def _render_to(self, output_dir, context, src_dir):
        """Recursively walk the src tree, and copy/render files across to the output_dir."""

        for src in src_dir.iterdir():
            if src.name in self.EXCLUDES or src.name.startswith("."):
                continue

            if src.is_dir():
                output_subdir = output_dir / src.name
                self._render_to(output_subdir, context, src)
            else:
                dst = output_dir / src.name
                if not dst.parent.exists():
                    dst.parent.mkdir()

                if src.suffix in [".tmpl", ".j2"]:
                    dst = output_dir / src.stem
                    relative_template_path = src.relative_to(self.directory)
                    template = self.environment.get_template(
                        str(relative_template_path)
                    )
                    content = template.render(**context)
                    dst.write_text(content)
                else:
                    shutil.copyfile(src, dst)

    def render(self, output_dir, form_data):
        """Render the templated code to output_dir using form_data as context."""
        context = copy.deepcopy(form_data)

        for codelist_key in self.codelist_keys:
            codelist = context[codelist_key]
            assert "slug" in codelist
            path = self.write_codelist(output_dir, codelist_key, codelist["slug"])

            # add path to context
            codelist["path"] = str(path.relative_to(output_dir))

        self._render_to(output_dir, context, self.directory)


@transaction.atomic()
def submit_analysis(
    *,
    analysis,
    backend,
    creator,
    project,
    get_opencodelists_api=_get_opencodelists_api,
    force=False,
):
    """
    Create all the parts needed for an analysis

    This will stay in job-server while create_commit() is intended to move to
    an external service in the future.
    """
    # TODO: wrap form kwargs up in a dataclass?

    # create an AnalysisRequest instance so we have a PK to use in various
    # places, but we don't save it until we've written the commit and pushed
    # it, so we can create the JobRequest this object needs
    analysis_request = AnalysisRequest(
        project=project,
        created_by=creator,
        title=analysis.title,
        template_data=asdict(analysis),
    )

    # update the Analysis structure so we can pass around a single object
    # if/when we pull the create_commit function out into another service
    # this structure would be the JSON we send over
    analysis.identifier = analysis_request.pk

    sha, project_yaml = create_commit(
        analysis,
        force=force,
        get_opencodelists_api=get_opencodelists_api,
        template_repo=settings.INTERACTIVE_TEMPLATE_REPO,
    )

    job_request = project.interactive_workspace.job_requests.create(
        backend=backend,
        created_by=creator,
        sha=sha,
        project_definition=project_yaml,
        force_run_dependencies=True,
        requested_actions=["run_all"],
    )

    analysis_request.job_request = job_request
    analysis_request.save()

    # TODO: notify someone about output checking?
    # waiting to find out what this should be
    # issue_url = create_issue(analysis_request.pk, job_server_url=url)
    # notify_analysis_request_submitted(analysis_request, issue_url)

    # TODO: notify the user?
    # send_analysis_request_confirmation_email(
    #     analysis_request.user.email, analysis_request
    # )
    return analysis_request


# MOVE TO EXTERNAL SERVICE


def clean_working_tree(path):
    """Remove all files (except .git)"""
    for f in path.glob("**/*"):
        relative = f.relative_to(path)

        if str(relative) == ".git" or str(relative).startswith(".git/"):
            continue

        print(f, relative)

        f.unlink() if f.is_file() else shutil.rmtree(f)


def commit_and_push(working_dir, analysis, force=False):
    force_args = ["--force"] if force else []

    git("add", ".", cwd=working_dir)

    second_codelist = ""
    if analysis.codelist_2:
        second_codelist = f" and codelist {analysis.codelist_2.slug}"
    msg = (
        f"Codelist {analysis.codelist_1.slug}{second_codelist} ({analysis.identifier})"
    )

    git(
        # -c arguments are instead of having to having to maintain stateful git config
        "-c",
        "user.email=interactive@opensafely.org",
        "-c",
        "user.name=OpenSAFELY Interactive",
        "commit",
        "--author",
        f"{analysis.created_by} <{analysis.created_by}>",
        "-m",
        msg,
        cwd=working_dir,
    )
    ps = git("rev-parse", "HEAD", capture_output=True, cwd=working_dir)
    commit_sha = ps.stdout.strip()

    # this is an super important step, makes it much easier to track commits
    git("tag", analysis.identifier, *force_args, cwd=working_dir)

    # push to main. Note: we technically wouldn't need this from a pure git
    # pov, as a tag would be enough, but job-runner explicitly checks that
    # a commit is on the branch history, for security reasons
    git("push", "origin", "main", "--force-with-lease", cwd=working_dir)

    # push the tag once we know the main push has succeeded
    git("push", "origin", analysis.identifier, *force_args, cwd=working_dir)
    return commit_sha


def create_commit(
    analysis,
    template_repo,
    force=False,
    get_opencodelists_api=_get_opencodelists_api,
):
    if not force:
        # check this commit does not already exist
        raise_if_commit_exists(analysis.repo, analysis.identifier)

    analysis_name = "v2"

    # 1. create tempdir with AR.pk suffix
    suffix = f"template-{analysis.identifier}"
    with tempfile.TemporaryDirectory(suffix=suffix) as working_dir:
        working_dir = Path(working_dir)

        # 2. clone the given analysis code template repo to tempdir
        git("clone", "--depth", "1", template_repo, working_dir)

        # 3. set up analysis templating for this analysis
        template_dir = working_dir / "templates" / analysis_name

        if not template_dir.exists():
            raise RuntimeError(
                f"interactive template repo { template_repo } does not have a templates/{analysis_name} directory"
            )

        codelists = ["codelist_1"]
        if analysis.codelist_2:
            codelists.append("codelist_2")

        analysis_template = AnalysisTemplate(
            template_dir, codelists, get_opencodelists_api
        )

        suffix = f"repo-{analysis.identifier}"
        with tempfile.TemporaryDirectory(suffix=suffix) as repo_dir:
            repo_dir = Path(repo_dir)

            # 4. clone the given interactive repo
            git("clone", "--depth", "1", analysis.repo, repo_dir)

            # 5. clear working directory because each analysis is fresh set of files
            clean_working_tree(repo_dir)

            # 6. render the files into the interactive repo
            analysis_template.render(repo_dir, asdict(analysis))

            # 7. write a commit to the given interactive repo
            sha = commit_and_push(repo_dir, analysis)

            # 8. return contents of project.yaml (from disk) and sha
            project_yaml = (repo_dir / "project.yaml").read_text()

    return sha, project_yaml


def download_codelist(slug, path, get_opencodelists_api=_get_opencodelists_api):
    """Download the contents of a codelist."""
    content = get_opencodelists_api().get_codelist(slug)

    path.write_text(content)


def git(*args, check=True, text=True, **kwargs):
    """
    Wrapper around subprocess.run for git commands.

    Changes the defaults: check=True and text=True, and prints the command run
    for logging.
    """
    cmd = ["git"] + [str(arg) for arg in args]

    cwd = kwargs.get("cwd", os.getcwd())
    token = settings.GITHUB_WRITEABLE_TOKEN or "*** no token ***"  # avoid a token of ""
    cleaned = [arg.replace(token, "*****") for arg in cmd]
    sys.stderr.write(f"{' '.join(cleaned)} (in {cwd})\n")

    # disable reading the user's gitconfig, to give us a more expected environment
    # when developing and testing locally.
    env = {"GIT_CONFIG_GLOBAL": "1"}

    return subprocess.run(cmd, check=check, text=text, env=env, **kwargs)


def raise_if_commit_exists(repo, tag):
    ps = git(
        "ls-remote",
        "--tags",
        repo,
        f"refs/tags/{tag}",
        capture_output=True,
    )
    if ps.stdout != "":
        raise Exception(f"Commit for {tag} already exists in {repo}")
