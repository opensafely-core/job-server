import pytest

from jobserver.authorization import StaffAreaAdministrator, has_role
from jobserver.nav import NavItem, iter_nav

from ...factories import UserFactory


def test_iter_nav_all_items(rf):
    request = rf.get("/")
    request.user = UserFactory()

    items = [
        NavItem(name="Event Log", url_name="job-list"),
        NavItem(name="Status", url_name="status"),
    ]

    output = list(iter_nav(items, request, lambda url: url == "/status/"))

    assert output == [
        {
            "name": "Event Log",
            "is_active": False,
            "url": "/event-log/",
        },
        {
            "name": "Status",
            "is_active": True,
            "url": "/status/",
        },
    ]


@pytest.mark.parametrize(
    "roles,expected",
    [
        (
            [StaffAreaAdministrator],
            [
                {
                    "name": "Always Shown",
                    "is_active": True,
                    "url": "/status/",
                },
                {
                    "name": "Only Shown for CoreDevs",
                    "is_active": False,
                    "url": "/staff/users/",
                },
            ],
        ),
        (
            [],
            [
                {
                    "name": "Always Shown",
                    "is_active": True,
                    "url": "/status/",
                }
            ],
        ),
    ],
    ids=["both_nav_items", "one_nav_item"],
)
def test_iter_nav_optional_items(rf, roles, expected):
    request = rf.get("/")
    request.user = UserFactory(roles=roles)

    items = [
        NavItem(name="Always Shown", url_name="status"),
        NavItem(
            name="Only Shown for CoreDevs",
            url_name="staff:user-list",
            predicate=lambda request: has_role(request.user, StaffAreaAdministrator),
        ),
    ]

    output = list(iter_nav(items, request, lambda url: url == "/status/"))

    assert output == expected
