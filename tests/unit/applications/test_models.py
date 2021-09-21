from ...factories import ResearcherRegistrationFactory


def test_job_str():
    researcher = ResearcherRegistrationFactory()

    assert str(researcher) == researcher.name
