import yaml

from .github import get_file


def load_yaml(content):
    return yaml.safe_load(content)


def get_actions(repo, branch):
    """Get actions from project.yaml for this Workspace"""
    content = get_file(repo, branch)
    if content is None:
        return {}

    project = load_yaml(content)

    for action, children in project["actions"].items():
        needs = children.get("needs", []) if children else []
        yield action, {"needs": needs}
