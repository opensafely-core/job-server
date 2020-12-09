import yaml

from .github import get_file


def load_yaml(content):
    return yaml.safe_load(content)


def get_actions(repo, branch, status_lut):
    """Get actions from project.yaml for this Workspace"""
    content = get_file(repo, branch)
    if content is None:
        raise Exception("Could not find project.yaml")

    project = load_yaml(content)

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
