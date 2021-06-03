from .github import is_member_of_org


def can_run_jobs(user):
    """
    Given User can run Jobs on the platform

    This is a short term (🤞) hack-adjacent way to enable our demo workflow
    before we can introduce proper role support (blocked by onboarding not
    having been built yet), and drive GitHub Org membership from job-server.
    """
    if not user.is_authenticated:
        return False

    # ensure the User is in an Org
    if not user.orgs.exists():
        return False

    gh_org = user.orgs.first().github_orgs[0]
    return is_member_of_org(gh_org, user.username)
