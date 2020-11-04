from jobserver.templatetags.status_tools import status_icon


def test_statusicon_running_status():
    output = status_icon("Running")

    assert 'class="spinner"' in output


def test_statusicon_known_status():
    output = status_icon("Succeeded")

    assert "color:green" in output
    assert 'data-icon="check"' in output


def test_statusicon_unknown_status():
    output = status_icon("duck")

    assert "color:grey" in output
    assert 'data-icon="question-circle"' in output
