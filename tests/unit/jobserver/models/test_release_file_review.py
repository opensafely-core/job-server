import pytest
from django.db import IntegrityError

from tests.factories import ReleaseFileReviewFactory


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_releasefilereview_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReleaseFileReviewFactory(**{field: None})
