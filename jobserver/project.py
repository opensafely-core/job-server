import yaml

from .github import get_branch, get_file


def get_actions(project, status_lut):
    """Get actions from project.yaml for this Workspace"""
    # ensure there's always a run_all action
    if "run_all" not in project["actions"]:
        project["actions"]["run_all"] = {"needs": list(project["actions"].keys())}

    for action, children in project["actions"].items():
        needs = children.get("needs", []) if children else []

        # handle needs being defined but empty
        if needs is None:
            needs = []

        # get latest status for this action from the lookup table
        status = status_lut.get(action, "-")

        yield {"name": action, "needs": sorted(needs), "status": status}


def get_project(org, repo, branch):
    content = get_file(org, repo, branch)

    if content is not None:
        return content

    if get_branch(org, repo, branch) is None:
        raise Exception(f"Missing branch: '{branch}'")

    raise Exception("Could not find project.yaml")


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


def load_yaml(content):
    return yaml.safe_load(content)


def render_definition(content, link_func):
    """
    Build a HTML version of the given project.yaml content

    In the future it might be eaiser to consume a parsed version of a
    project.yaml but since we're only convert the script-looking substrings
    currently this seems like the quicker path.
    """
    lines = content.split("\n")

    for i, line in enumerate(lines):
        if "run:" not in line:
            continue

        # recreate the spaces removed inside parse_run_line()
        lines[i] = " ".join(link_run_scripts(line, link_func))

    # replace newlines with <br /> elements so the normal newlines aren't
    # collapsed when the browser renders them.
    definition = "<br/>".join(lines)

    return definition
