import pytest

from jobserver.authorization import CoreDeveloper, has_role
from jobserver.nav import NavItem, iter_nav

from ...factories import UserFactory


def test_iter_nav_all_items(rf):
    request = rf.get("/")
    request.user = UserFactory()

    items = [
        NavItem(name="Orgs", url_name="org-list"),
        NavItem(name="Event Log", url_name="job-list"),
    ]

    output = list(iter_nav(items, request, lambda url: url == "/orgs/"))

    assert output == [
        {
            "name": "Orgs",
            "is_active": True,
            "url": "/orgs/",
        },
        {
            "name": "Event Log",
            "is_active": False,
            "url": "/event-log/",
        },
    ]


@pytest.mark.parametrize(
    "roles,expected",
    [
        (
            [CoreDeveloper],
            [
                {
                    "name": "Always Shown",
                    "is_active": True,
                    "url": "/orgs/",
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
                    "url": "/orgs/",
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
        NavItem(name="Always Shown", url_name="org-list"),
        NavItem(
            name="Only Shown for CoreDevs",
            url_name="staff:user-list",
            predicate=lambda request: has_role(request.user, CoreDeveloper),
        ),
    ]

    output = list(iter_nav(items, request, lambda url: url == "/orgs/"))

    assert output == expected
