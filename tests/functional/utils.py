from tests.factories import UserFactory


def login_user(context, client, live_server, roles=None):
    """
    Helper function to log a user (with optional roles) into the Playwright browser context.

    Use as follows:
    user = login_user(
        context=context,
        client=client,
        live_server=live_server,
        roles=[
            role_factory(permission=Permission.STAFF_AREA_ACCESS),
            role_factory(permission=Permission.PROJECT_CREATE),
            role_factory(permission=Permission.ORG_CREATE),
        ],
    )
    """
    if roles:
        user = UserFactory(roles=roles)
    else:
        user = UserFactory()

    client.force_login(user)

    context.add_cookies(
        [
            {
                "name": "sessionid",
                "value": client.cookies["sessionid"].value,
                "url": live_server.url,
            }
        ]
    )

    return user
