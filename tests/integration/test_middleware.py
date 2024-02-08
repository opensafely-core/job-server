def test_browser_reload_middleware_with_get(client, settings):
    settings.DEBUG = True
    response = client.get("/login/")
    assert (
        b'django-browser-reload/reload-listener.js" data-worker-script-path'
        in response.content
    )


def test_browser_reload_middleware_with_post(client, settings):
    settings.DEBUG = True
    response = client.post("/login/")
    assert (
        b'django-browser-reload/reload-listener.js" data-worker-script-path'
        not in response.content
    )
