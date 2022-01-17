from jobserver.slacks import notify_new_user


def notify_on_new_user(user, is_new, *args, **kwargs):
    if not is_new:
        return
    notify_new_user(user)


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
