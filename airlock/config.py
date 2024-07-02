from environs import Env


env = Env()


ORG_OUTPUT_CHECKING_REPOS = {
    "university-of-bristol": {
        "org": "ebmdatalab",
        "repo": "opensafely-output-review-bristol",
    },
    "default": {
        "org": "ebmdatalab",
        "repo": env.str(
            "DEFAULT_OUTPUT_CHECKING_REPO", default="opensafely-output-review"
        ),
    },
}
