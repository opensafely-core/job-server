from django.urls import reverse

from ...factories import AnalysisRequestFactory, UserFactory


def test_get_absolute_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_absolute_url()

    assert url == reverse(
        "interactive:analysis-detail",
        kwargs={
            "org_slug": analysis_request.project.org.slug,
            "project_slug": analysis_request.project.slug,
            "pk": analysis_request.pk,
        },
    )


def test_get_codelist_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_codelist_url()

    assert (
        url
        == f"https://www.opencodelists.org/codelist/{analysis_request.codelist_slug}"
    )


def test_get_stuff_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_staff_url()

    assert url == reverse(
        "staff:analysis-request-detail", kwargs={"pk": analysis_request.pk}
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
