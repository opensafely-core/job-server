import time

from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from social_core.pipeline.partial import partial
from social_core.storage import UserMixin
from social_django.models import UserSocialAuth

from jobserver.models import get_or_create_user
from jobserver.slacks import notify_new_user


@partial
def pipeline(response, strategy, *args, **kwargs):
    """
    Combined auth pipeline for GitHub OAuth

    This is a reduction of our previous step-by-step pipeline which leant
    heavily on Python Social Auth (and Social Django) functions.

    We still lean on PSA to run the pipeline, handling the OAuth dance with
    GitHub and calling the necessary functions to log a user in for Django.  As
    such we return the `social` and `user` keys to facilitate that.
    """
    uid = response["id"]

    social = UserSocialAuth.objects.filter(uid=uid).first()
    if social and social.user:
        # existing user, we're done here
        return {
            # included so login can be called with the correct auth backend
            "social": social,
            "user": social.user,
        }

    # brand new user, create everything.
    # the UserSocialAuth.user FK doesn't allow us to have a social without a
    # user so we can ignore that path

    name = response["name"] or strategy.request.POST.get("name")
    if not name:
        # if name is missing from response and POST data
        current_partial = kwargs.get("current_partial")
        url = reverse("require-name") + f"?partial_token={current_partial.token}"
        return redirect(url)

    # clean the username to match how PSA does it in
    # social_core.pipeline.user.get_username
    username = UserMixin.clean_username(response["login"])

    with transaction.atomic():
        user, _ = get_or_create_user(
            username,
            email=response["email"],
            fullname=name,
            update_fields=["email", "fullname"],
        )

        # store some raw data from the response
        extra_data = {
            "auth_time": int(time.time()),
            "id": uid,
            "expires": response.get("expires", None),
            "login": response["login"],
            "access_token": response["access_token"],
            "token_type": response["token_type"],
        }

        social = UserSocialAuth.objects.create(
            user=user, uid=uid, provider="github", extra_data=extra_data
        )

    notify_new_user(user)

    return {
        # included so login can be called with the correct auth backend
        "social": social,
        "user": social.user,
    }
