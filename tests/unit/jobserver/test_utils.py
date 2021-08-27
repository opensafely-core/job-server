import pytest

from jobserver.authorization import OutputChecker
from jobserver.models import Job
from jobserver.utils import dotted_path, set_from_qs

from ...factories import JobFactory


def test_dotted_path():
    assert dotted_path(OutputChecker) == "jobserver.authorization.roles.OutputChecker"


@pytest.mark.django_db
def test_set_from_qs():
    job1 = JobFactory(status="test")
    job2 = JobFactory(status="success")
    job3 = JobFactory(status="success")

    # check using the default field of pk
    output = set_from_qs(Job.objects.all())
    assert output == {job1.pk, job2.pk, job3.pk}

    # check using the field kwarg
    output = set_from_qs(Job.objects.all(), field="status")
    assert output == {"test", "success"}
