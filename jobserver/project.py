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


def get_project(repo, branch):
    content = get_file(repo, branch)

    if content is not None:
        return content

    if get_branch(repo, branch) is None:
        raise Exception(f"Missing branch: '{branch}'")

    raise Exception("Could not find project.yaml")


def load_yaml(content):
    return yaml.safe_load(content)
