# Testing

## General Layout
Tests live in the `tests` directory split into the three types of layers of test they cover.

Test functions are named `test_nameofthing_part_that_you_are_testing`, so the function `frob_the_wizzle` being tested without the correct permissions should have the test `test_frobthewizzle_with_no_permission`.
This might not be the best naming scheme but we want to be consistent above all else to aid in test discoverability for developers.

We aim to use the [Arrange/Assert/Act Pattern](https://java-design-patterns.com/patterns/arrange-act-assert/) for organising code within a test.

Docstrings and comments explaining why a test works the way it does are highly recommended, eg why did you set it up this way? Why are you testing this exit condition? etc.

Tests should be fast where possible.


## Testing Pyramid
Job Server uses a three layer testing pyramid, with the following layers from top to bottom:
* End-to-End
* Integration
* Unit

Below we describe how we draw the lines between each of those layers.

Much like the developer tooling at Bennett Institute for Applied Data Science we define these layers as an ideal guide that should be adhered by default, but in the knowledge that things can deviate if there is a good reason.


### Unit Tests
**Directory:** `tests/unit`

These are the current majority of the tests, something we expect to continue for some time.

Test modules mirror their non-testing counterparts, so tests covering functions in `jobserver/some_path/foo.py` live in `tests/jobserver/some_path/foo.py`.

Each function/class should have at least one test, ideally one for each exit condition.

For views we use [`RequestFactory` instances](https://docs.djangoproject.com/en/3.2/topics/testing/advanced/#the-request-factory) as the default testing method, reserving Client instances for Integration tests (more below), testing the Python responses of views under test.

*Author's Note:* in an ideal world testing views would be bumped up to Integration tests since they typically test across at least one boundary, the database.
However, since testing without the database in a Django codebase is not a trivial job we've decided to stick with the flow and treat them like unit tests.


### Integration
**Directory:** `tests/integration`

Integration tests live at a level above unit tests, testing the combination of various pieces.

Each view should have at least one integration test for the happy path.
These tests should use [`Client` instances](https://docs.djangoproject.com/en/3.2/topics/testing/tools/#the-test-client).
Ideally these tests would avoid mocking.

This lets us test views with all the surrounding parts turned: URL routing, middleware, etc.


### End-to-End
**Directory:** `tests/e2e`

We don't currently have any end-to-end tests but with the upcoming addition of onboarding it's clear we need a way to test across multiple views.

The expectation is that these tests will check user flows work as expected, eg "As a user who has not signed up before who has received an invite email I can…".  These tests would likely like Client instances.


## Tooling
We use [coverage.py](https://coverage.readthedocs.io/) to check test coverage on the code base and require 100% coverage for CI to pass.

[FactoryBoy](https://factoryboy.readthedocs.io/) provides most of our model factories for easy creation of model instances inside tests.
Where FactoryBoy isn't a good fit a factory class should attempt to work as much like a FactoryBoy class factory as possible.
`ReleaseFactory` is a good example of where we've already done that.

[PyTest fixtures](https://docs.pytest.org/en/6.2.x/fixture.html) provide useful helpers for the tests.
They are also the ideal place to build up combinations of factorys, eg [the `user` fixture](https://github.com/opensafely-core/job-server/blob/62a376aa120542d246efd854bc1d4de1b70a60cf/tests/conftest.py#L63-L77) which provides a User with associated Org.
We also provide DRF's testing tools as fixtures to mirror pytest-django.

[pytest-django](https://pytest-django.readthedocs.io/en/latest/) is the bridge between pytest and Django, exposing various Django testing tools (Client, RequestFactory, etc) as fixtures.


## Useful Flows
`just test` will run the tests as CI does, however as the suite grows this gets slower over time.
Below is [very!] non-exhaustive list of useful methods we have found to make running tests easier.

* `pytest -k <partial test name>`: working on a new view? `pytest -k yourviewname` is a quick way to only run those tests.
* `pytest --lf`: run the tests which failed in the last run, good for iteratively fixing tests.
* `pytest -x`: stop at the first test failure, good for iteratively working through known broken tests.
