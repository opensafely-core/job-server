from redirects.middleware import RedirectsMiddleware

from ...factories import ProjectFactory, RedirectFactory, WorkspaceFactory


def get_response(request):
    return "no match"


def test_redirectsmiddleware_known_url_via_prefix(rf):
    project = ProjectFactory()

    RedirectFactory(old_url="/abc/123/", project=project)
    RedirectFactory(old_url="/org/project/workspace/", workspace=WorkspaceFactory())

    request = rf.get("/abc/123/test")

    response = RedirectsMiddleware(get_response)(request)

    assert response.url == project.get_absolute_url() + "test"


def test_redirectsmiddleware_known_url_with_direct_match(rf):
    project = ProjectFactory()

    RedirectFactory(old_url="/abc/123/", project=project)
    RedirectFactory(old_url="/abc/123/test/", workspace=WorkspaceFactory())

    request = rf.get("/abc/123/")

    response = RedirectsMiddleware(get_response)(request)

    assert response.url == project.get_absolute_url()


def test_redirectsmiddleware_unknown_url(rf):
    request = rf.get("/")

    response = RedirectsMiddleware(get_response)(request)

    assert response == "no match"
