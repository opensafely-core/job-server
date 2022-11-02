from jobserver.slacks import notify_new_user


def notify_on_new_user(user, is_new, *args, **kwargs):
    if not is_new:
        return
    notify_new_user(user)


def set_fullname(user, details, *args, **kwargs):
    """
    Set a User's fullname from GitHub if it's not already set

    By default social_core.pipeline.user.user_details takes the values from
    the social backend, GitHub for us, and overwrites the data in a given User
    instance.  We want to let users update (or set) their name on our service
    without involving GitHub and not have it overwritten each time they log in.

    We've added the fullname field to the SOCIAL_AUTH_PROTECTED_USER_FIELDS
    setting which stops social_core's user_details function from overwriting
    our version, and this function fills it if it's not already set.
    """
    if not user.fullname:
        user.fullname = details.get("fullname", "")
        user.save()


def set_notifications_email(user, *args, **kwargs):
    """
    Set a User's notifications_email if it's not already set

    When a User first signs up to the service they don't have their
    notifications_email set, so we copy the value passed to us from GitHub to
    that value.
    """
    if not user.notifications_email:
        user.notifications_email = user.email
        user.save()
