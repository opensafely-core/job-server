from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import YamlLexer

from .github import _get_github_api
from .opencodelists import _get_opencodelists_api
from .permissions.cohortextractor import project_is_permitted_to_use_cohortextractor
from .permissions.sqlrunner import project_is_permitted_to_use_sqlrunner


class ActionPermissionError(Exception):
    """Raised when a job tries to run an action for which the project does not have
    permission."""


def check_cohortextractor_permission(project, config):
    run_commands = [v.run.raw for v in config.actions.values()]
    if not any("cohortextractor" in command for command in run_commands):
        # No need to check permission if project does not use cohort-extractor.
        return
    if not project_is_permitted_to_use_cohortextractor(project):
        msg = "This project does not have permission to run cohort-extractor jobs"
        raise ActionPermissionError(msg)


def check_sqlrunner_permission(project, config):
    run_commands = [v.run.raw for v in config.actions.values()]
    if not any("sqlrunner" in command for command in run_commands):
        # No need to check permission if project does not use SQL Runner.
        return
    if not project_is_permitted_to_use_sqlrunner(project):
        msg = "This project does not have permission to run SQL Runner jobs"
        raise ActionPermissionError(msg)


def get_actions(config):
    """Get actions from a pipeline config for this Workspace"""
    for action, children in config.actions.items():
        needs = sorted(children.needs)

        yield {"name": action, "needs": needs}

    # ensure there's always a run_all action
    if "run_all" not in config.actions:
        all_actions = list(config.actions.keys())
        yield {"name": "run_all", "needs": all_actions}


def get_project(org, repo, branch, get_github_api=_get_github_api):
    github_api = get_github_api()

    content = github_api.get_file(org, repo, branch)

    if content is not None:
        return content

    if github_api.get_branch(org, repo, branch) is None:
        raise Exception(f"Missing branch: '{branch}'")

    raise Exception("Could not find project.yaml")


def get_codelists_status(
    org,
    repo,
    branch,
    get_github_api=_get_github_api,
    get_opencodelists_api=_get_opencodelists_api,
):
    github_api = get_github_api()
    opencodelists_api = get_opencodelists_api()

    codelists_content = (
        github_api.get_file(org, repo, branch, filepath="codelists/codelists.txt"),
        github_api.get_file(org, repo, branch, filepath="codelists/codelists.json"),
    )

    if any(content is None for content in codelists_content):
        if github_api.get_branch(org, repo, branch) is None:
            raise Exception(f"Missing branch: '{branch}'")

        if github_api.get_file(org, repo, branch, filepath="codelists") is not None:
            raise Exception("Could not find codelists.txt or codelists.json")
        # Missing codelists.txt/codelists.json files are only an issue if the
        # codelists directory exists. If the repo contains no codelists,
        # there's nothing to check.
        return "ok"

    codelists_check = opencodelists_api.check_codelists(*codelists_content)
    return codelists_check["status"]


def link_run_scripts(line, link_func):
    """
    Find scripts in a run: line and wrap with links

    Given a line of text try to find script-looking paths and convert them to
    HTML links using the given linking function.
    """
    # split with parentheses to capture delimiter
    parts = line.split(" ")

    for part in parts:
        if part.startswith("-"):
            # ignore CLI switches
            yield part
            continue

        if "output" in part:
            # output in path sounds like an output location
            yield part
            continue

        if "/" not in part:
            # assume all script calls use a subdirectory
            yield part
            continue

        # keep the original token for the label
        label = part

        # strip common prefixes which aren't of use to us when linking to the
        # blob on GitHub
        part = part.removeprefix("/workspace/")
        part = part.removeprefix("./")
        part = part.removeprefix("/")

        url = link_func(part)
        yield f'<a href="{url}">{label}</a>'


def map_run_scripts_to_links(content, link_func):
    """
    Build a mapping of script-looking substrings to HTML link

    We want to link scripts in project.yamls to their files on GitHub, however
    we can't replace the script names in YAML with <a>s as pygments will wrap
    it in its output.  So instead this function builds up a mapping with the
    original target for a run: as the key and the same line with scripts
    converted to links as the value.  That lets us turn a line which looks so:

        run: stata-mp:latest analysis/flow_chart_af_population.do af_population_flowchart

    into a mapping like this:

        {"stata-mp:latest analysis/flow_chart_af_population.do af_population_flowchart": "<a href="…">stata-mp:latest analysis/flow_chart_af_population.do af_population_flowchart</a>"}

    This lets us then mutate the HTML output from pygments.
    """
    # break up the original content into lines
    lines = content.split("\n")

    # gather only lines with a run: stanza
    run_lines = [line.strip() for line in lines if "run:" in line]

    # strip the run prefixes so the resulting line can be used as a key later
    # the HTML generated by pygments puts the `run:` portion in a different
    # <span> so we don't need to bother keeping it when replacing the target
    # portion.
    run_lines = [line.removeprefix("run:").strip() for line in run_lines]

    # build up an iterable of tuples with (original, replacement)
    links_map = (
        (line, " ".join(link_run_scripts(line, link_func))) for line in run_lines
    )

    # finally convert to a dictionary so we can use it as a mapping
    return dict(links_map)


def render_definition(content, link_func):
    """
    Build a HTML version of the given project.yaml content

    In the future it might be eaiser to consume a parsed version of a
    project.yaml but since we're only converting the script-looking substrings
    currently this seems like the quicker path.
    """
    # convert the YAML content to HTML with pygments
    output = highlight(
        content.strip(),
        YamlLexer(),
        HtmlFormatter(cssclass="card-body my-0 rounded-0 highlight"),
    )

    # replace the script lines with their links
    links_map = map_run_scripts_to_links(content, link_func)
    for script, link in links_map.items():
        output = output.replace(script, link)

    return output
