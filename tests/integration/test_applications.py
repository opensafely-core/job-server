import factory
from django.urls import reverse

from ..factories import UserFactory


def url_builder(application):
    """
    build a URL function to make referencing URLs easier

    We need to tell the client to reference a given page and also check that
    it redirected to the next page.  Each URL uses the same application hash,
    so rather than duplicating that for each test this function builder and
    the function it creates allows us to call it with url("page-key").
    """

    def url(page_key):
        return f"/applications/{application.pk_hash}/page/{page_key}/"

    return url


def test_successful_application(client, mailoutbox, slack_messages):
    user = UserFactory()

    client.force_login(user)

    # start
    response = client.get(reverse("applications:start"))
    assert response.status_code == 200

    # terms GET
    response = client.get(reverse("applications:terms"))
    assert response.status_code == 200

    # terms POST to start the application
    response = client.post(reverse("applications:terms"), follow=True)
    assert response.status_code == 200
    assert len(slack_messages) == 1

    # get the application and build the URL function to make our lives easier
    # as we go through each page
    application = user.applications.order_by("-created_at").first()
    url = url_builder(application)

    # check the redirect for POSTing to terms worked, needs to use the url()
    # function we built above so can't be grouped with the rest of the page
    # assertions
    assert response.redirect_chain == [(url("contact-details"), 302)]

    # contact details
    data = {
        "full_name": "Testing McTesterson",
        "email": "test@example.com",
        "telephone": factory.Faker("phone_number"),
        "job_title": "Head of Testing",
        "team_name": "Testers",
        "organisation": "ACME",
    }
    response = client.post(url("contact-details"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("commercial-involvement"), 302)]
    page = application.contactdetailspage
    assert page.full_name
    assert page.email
    assert page.telephone
    assert page.job_title
    assert page.team_name
    assert page.organisation

    # commercial involvement
    data = {
        "details": "No commercial involvement",
    }
    response = client.post(url("commercial-involvement"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("study-information"), 302)]
    page = application.commercialinvolvementpage
    assert page.details

    # study-information
    data = {
        "study_name": "Title for this study",
        "study_purpose": "Long form technical message about what this study is about",
    }
    response = client.post(url("study-information"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("study-purpose"), 302)]
    page = application.studyinformationpage
    assert page.study_name
    assert page.study_purpose

    # study-purpose
    data = {
        "description": "Title for this study",
        "is_covid_prevention": "",
        "is_risk_from_covid": "yes",
        "is_post_covid_health_impacts": "",
        "is_covid_vaccine_eligibility_or_coverage": "yes",
        "is_covid_vaccine_effectiveness_or_safety": "",
        "is_other_impacts_of_covid": "yes",
        "author_name": "Author McAuthorson",
        "author_email": "author@example.com",
        "author_organisation": "Author Organisation",
    }
    response = client.post(url("study-purpose"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("study-data"), 302)]
    page = application.studypurposepage
    assert page.description
    assert not page.is_covid_prevention
    assert page.is_risk_from_covid
    assert not page.is_post_covid_health_impacts
    assert page.is_covid_vaccine_eligibility_or_coverage
    assert not page.is_covid_vaccine_effectiveness_or_safety
    assert page.is_other_impacts_of_covid
    assert page.author_name
    assert page.author_email
    assert page.author_organisation

    # study-data
    data = {
        "need_record_level_data": "True",
        "data_meets_purpose": "",
    }
    response = client.post(url("study-data"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("datasets"), 302)]
    page = application.studydatapage
    assert page.need_record_level_data
    assert not page.data_meets_purpose

    # datasets
    data = {
        "needs_icnarc": "yes",
        "needs_isaric": "",
        "needs_ons_cis": "yes",
        "needs_phosp": "",
        "needs_ukrr": "yes",
    }
    response = client.post(url("datasets"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("record-level-data"), 302)]
    page = application.datasetspage
    assert page.needs_icnarc
    assert not page.needs_isaric
    assert page.needs_ons_cis
    assert not page.needs_phosp
    assert page.needs_ukrr

    # record-level-data
    data = {
        "record_level_data_reasons": "reasons for record level data",
    }
    response = client.post(url("record-level-data"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("type-of-study"), 302)]
    page = application.recordleveldatapage
    assert page.record_level_data_reasons

    # type-of-study (research)
    data = {
        "is_study_research": "yes",
        "is_study_service_evaluation": "",
        "is_study_audit": "",
    }
    response = client.post(url("type-of-study"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("references"), 302)]
    page = application.typeofstudypage
    assert page.is_study_research
    assert not page.is_study_service_evaluation
    assert not page.is_study_audit

    # reset the type of study so we can also test the service eval/study audit flow
    application.typeofstudypage.is_study_research = False
    application.typeofstudypage.is_study_service_evaluation = False
    application.typeofstudypage.is_study_audit = False
    application.typeofstudypage.save()
    application.refresh_from_db()

    # type-of-study (service eval or study audit)
    data = {
        "is_study_research": "",
        "is_study_service_evaluation": "yes",
        "is_study_audit": "",
    }
    response = client.post(url("type-of-study"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("service-evaluation-audit"), 302)]
    page = application.typeofstudypage
    assert not page.is_study_research
    assert page.is_study_service_evaluation
    assert not page.is_study_audit

    # references
    data = {
        "hra_ires_id": "abc123",
        "hra_rec_reference": "abc123",
        "institutional_rec_reference": "abc123",
    }
    response = client.post(url("references"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("service-evaluation-audit"), 302)]
    page = application.referencespage
    assert page.hra_ires_id
    assert page.hra_rec_reference
    assert page.institutional_rec_reference

    # service-evaluation-audit
    data = {
        "is_member_of_bennett_or_lshtm": "yes",
        "institutional_rec_reference": "abc123",
        "sponsor_name": "Sponsor McSponsorson",
        "sponsor_email": "sponsor@example.com",
        "sponsor_job_role": "Sponsor",
    }
    response = client.post(url("service-evaluation-audit"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("study-funding"), 302)]
    page = application.sponsordetailspage
    assert page.is_member_of_bennett_or_lshtm
    assert page.institutional_rec_reference
    assert page.sponsor_name
    assert page.sponsor_email
    assert page.sponsor_job_role

    # study-funding
    data = {
        "funding_details": "details for funding",
    }
    response = client.post(url("study-funding"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("team-details"), 302)]
    page = application.studyfundingpage
    assert page.funding_details

    # team-details
    data = {
        "team_details": "details about the team",
    }
    response = client.post(url("team-details"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("previous-ehr-experience"), 302)]
    page = application.teamdetailspage
    assert page.team_details

    # previous-ehr-experience
    data = {
        "previous_experience_with_ehr": "some experience with EHR",
    }
    response = client.post(url("previous-ehr-experience"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("software-development-experience"), 302)]
    page = application.previousehrexperiencepage
    assert page.previous_experience_with_ehr

    # software-development-experience
    data = {
        "evidence_of_coding": "some evidence of prior coding experience",
        "all_applicants_completed_getting_started": "True",
    }
    response = client.post(url("software-development-experience"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("sharing-code"), 302)]
    page = application.softwaredevelopmentexperiencepage
    assert page.evidence_of_coding
    assert page.all_applicants_completed_getting_started

    # sharing-code
    data = {
        "evidence_of_sharing_in_public_domain_before": "some evidence of sharing of sharing code before",
    }
    response = client.post(url("sharing-code"), data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(url("researcher-details"), 302)]
    page = application.sharingcodepage
    assert page.evidence_of_sharing_in_public_domain_before

    # add researcher
    data = {
        "name": "First Researcher",
        "job_title": "Researching",
        "email": "researcher@example.com",
        "github_username": "researcher",
        "does_researcher_need_server_access": "True",
        "telephone": factory.Faker("phone_number"),
        "phone_type": "iphone",
        "has_taken_safe_researcher_training": "True",
        "training_with_org": "ONS",
        "training_passed_at": "2020-07-08",
    }
    next_url = url("researcher-details")
    response = client.post(
        f"/applications/{application.pk_hash}/researchers/add/?next={next_url}",
        data,
        follow=True,
    )
    assert response.status_code == 200
    assert response.redirect_chain == [(url("researcher-details"), 302)]
    assert application.researcher_registrations.first().name == "First Researcher"

    # researcher-details
    response = client.get(url("researcher-details"))
    assert response.status_code == 200
    assert b"First Researcher" in response.content

    response = client.post(url("researcher-details"), follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [
        (f"/applications/{application.pk_hash}/confirmation/", 302)
    ]

    # confirmation
    assert len(slack_messages) == 1
    assert len(mailoutbox) == 0

    response = client.post(
        f"/applications/{application.pk_hash}/confirmation/", follow=True
    )
    assert response.status_code == 200
    assert response.redirect_chain == [("/applications/", 302)]

    assert len(slack_messages) == 2
    assert len(mailoutbox) == 1
