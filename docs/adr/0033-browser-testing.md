# Automated browser testing

Date: 2025-12

## Status

Accepted

## Context

We have unit tests that cover parts of our code, both frontend and backend.

However, those tests:

* primarily test frontend and backend in isolation
* do not regularly test user flows end-to-end, such as:
  * a user logging in, creating a new job request and later cancelling that
    same job request
  * a staff member logging in, changing another user's role, and that user
    being unable to make some change they previously could
* do enforce coverage for the backend tests, but not the frontend tests
  (though we currently have high coverage there)

Automated web browser testing of key user journeys end-to-end would be a
useful addition. Browser testing enables us to validate that those user
journeys continue to function as intended when making code changes, and
when upgrading dependencies. Adding browser tests would help reduces the
risk of deploying changes to production that unintentionally change user
functionality.

### Testing frameworks

There are several different testing frameworks available,
including Cypress, Selenium and Playwright. However, for developing Airlock,
the decision was made to use Playwright for its functional testing, and
those tests have been in place since early 2024.

Following from the work in Airlock, Team REX added Playwright tests to
OpenCodelists.

There are advantages in trying to keep the technology stack consistent
across projects: developers have fewer tools to learn, and there can be
sharing of expertise and experience across projects.

## Decision

We will add automated browser tests that are run with Python using
Playwright and pytest-django's `live_server` fixture to run against a
real Django server. This is how the Airlock tests work.

These tests will be run separately from the existing unit tests. This is
partly a design choice — browser tests are generally slower than unit
tests and we do not want to slow down the existing unit test suite — and
partly because of the differing fixture configuration needed as
mentioned above.

## Consequences

* We will have greater assurance that code or dependency changes do not
  result in unintended behaviour changes.
* These tests will need to be maintained, and updated if existing user
  journeys change, or the site design changes to break the existing
  Playwright selectors.
* We will need other tests for important user journeys not covered by
  the initially added tests.
* If we add other important user journeys, new tests will need to be
  added. We could consider addition of appropriate browser tests an
  acceptance criteria for issues involving new user journeys.
