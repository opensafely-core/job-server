from jobserver.templatetags.status_tools import status_icon


def test_statusicon_known_status():
    output = status_icon("Completed")

    assert "color:green" in output
    assert 'data-icon="check"' in output


def test_statusicon_unknown_status():
    output = status_icon("duck")

    assert "color:grey" in output
    assert 'data-icon="question-circle"' in output
