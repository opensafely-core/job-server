from django.utils import timezone

from staff.views.repos import RepoList


def test_workspacelist_success(rf, core_developer, mocker):
    request = rf.get("/")
    request.user = core_developer

    mocker.patch(
        "staff.views.repos.get_repos_with_dates",
        autospec=True,
        return_value=[
            {
                "name": "test",
                "url": "test",
                "is_private": True,
                "created_at": timezone.now(),
            }
        ],
    )

    response = RepoList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["repos"]) == 1
