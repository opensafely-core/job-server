from jobserver.authorization import OutputChecker
from jobserver.models import Job
from jobserver.utils import (
    build_spa_base_url,
    dotted_path,
    is_safe_path,
    set_from_qs,
    strip_whitespace,
)

from ...factories import JobFactory


def test_build_spa_base_url():
    base = build_spa_base_url("/a/page/with/file.csv", "with/file.csv")

    assert base == "/a/page/"


def test_dotted_path():
    assert dotted_path(OutputChecker) == "jobserver.authorization.roles.OutputChecker"


def test_is_safe_path_with_safe_path():
    assert is_safe_path("/")
    assert is_safe_path("/status/")


def test_is_safe_path_with_unsafe_path():
    assert not is_safe_path("https://steal-your-bank-details.com/")


def test_strip_whitespace():
    text = """
    testing text
    """

    output = strip_whitespace(text)

    assert output == "testing text"


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
