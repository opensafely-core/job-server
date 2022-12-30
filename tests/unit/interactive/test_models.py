from ...factories import AnalysisRequestFactory, UserFactory


def test_get_codelist_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_codelist_url()

    assert (
        url
        == f"https://www.opencodelists.org/codelist/{analysis_request.codelist_slug}"
    )


def test_str():
    analysis_request = AnalysisRequestFactory()

    assert (
        str(analysis_request)
        == f"{analysis_request.title} ({analysis_request.codelist_slug})"
    )


def test_visible_to_creator():
    analysis_request = AnalysisRequestFactory()

    assert analysis_request.visible_to(analysis_request.created_by)


def test_visible_to_staff(core_developer):
    analysis_request = AnalysisRequestFactory()

    assert analysis_request.visible_to(core_developer)


def test_visible_to_other_user():
    analysis_request = AnalysisRequestFactory()

    assert not analysis_request.visible_to(UserFactory())
