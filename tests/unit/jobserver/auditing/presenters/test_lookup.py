import pytest

from jobserver.auditing.presenters import project_members
from jobserver.auditing.presenters.exceptions import UnknownPresenter
from jobserver.auditing.presenters.lookup import get_presenter
from jobserver.models import AuditableEvent


def test_get_presenter_with_known_type():
    class Fake:
        type = AuditableEvent.Type.PROJECT_MEMBER_ADDED  # noqa: A003

    assert get_presenter(Fake()) == project_members.added


def test_get_presenter_with_unknown_type():
    class Fake:
        type = None  # noqa: A003

    with pytest.raises(UnknownPresenter):
        get_presenter(Fake())
