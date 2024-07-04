from django.conf import settings


ORG_OUTPUT_CHECKING_REPOS = {
    "university-of-bristol": {
        "org": "ebmdatalab",
        "repo": "opensafely-output-review-bristol",
    },
    "default": {
        "org": settings.DEFAULT_OUTPUT_CHECKING_GITHUB_ORG,
        "repo": settings.DEFAULT_OUTPUT_CHECKING_REPO,
    },
}


ORG_SLACK_CHANNELS = {"default": settings.DEFAULT_OUTPUT_CHECKING_SLACK_CHANNEL}
