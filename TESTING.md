# Testing

- [General Layout](#general-layout)
- [Testing Pyramid](#testing-pyramid)
  - [Unit Tests](#unit-tests)
  - [Integration](#integration)
  - [End-to-end](#end-to-end)
- [Tooling](#tooling)
- [Verified Fakes](#verified-fakes)
- [Useful Flows](#useful-flows)
- [Testing Releases](#testing-releases)

## General Layout
Tests live in the `tests` directory split into the three types of layers of test they cover.

Test functions are named `test_nameofthing_part_that_you_are_testing`, so the function `frob_the_wizzle` being tested without the correct permissions should have the test `test_frobthewizzle_with_no_permission`.
This might not be the best naming scheme but we want to be consistent above all else to aid in test discoverability for developers.

We aim to use the [Arrange/Assert/Act Pattern](https://java-design-patterns.com/patterns/arrange-act-assert/) for organising code within a test.

Docstrings and comments explaining why a test works the way it does are highly recommended, eg why did you set it up this way? Why are you testing this exit condition? etc.

Tests should be fast where possible.


## Testing Pyramid

Job Server uses a testing pyramid, with the following layers from top to bottom:

* Integration
* Unit

### Unit Tests
**Directory:** `tests/unit`

These are the current majority of the tests, something we expect to continue for some time.

Test modules mirror their non-testing counterparts, so tests covering functions in `jobserver/some_path/foo.py` live in `tests/jobserver/some_path/foo.py`.

Each function/class should have at least one test, ideally one for each exit condition.

For views we use [`RequestFactory` instances](https://docs.djangoproject.com/en/5.2/topics/testing/advanced/#the-request-factory) as the default testing method, reserving Client instances for Integration tests (more below), testing the Python responses of views under test.

*Author's Note:* in an ideal world testing views would be bumped up to Integration tests since they typically test across at least one boundary, the database.
However, since testing without the database in a Django codebase is not a trivial job we've decided to stick with the flow and treat them like unit tests.


### Integration
**Directory:** `tests/integration`

Integration tests live at a level above unit tests, testing the combination of various pieces.

Each view should have at least one integration test for the happy path.
These tests should use [`Client` instances](https://docs.djangoproject.com/en/5.2/topics/testing/tools/#the-test-client).
Ideally these tests would avoid mocking.

This lets us test views with all the surrounding parts turned on: URL routing, middleware, etc.

### Notes for test authors

We have a custom `@pytest.mark.slow_test` marker that should be used on test
that take more than about 0.1s to run. These are excluded from `just test` to
provide a quicker feedback loop.

All unit and integration tests have access to the database by default. You can
use the `db` fixture fixture to provide access to other tests if required. Or
search `enable_db_access_for_all_tests`to see how to enable it for a directory
(via conftest.py) or in a module.

Avoid writing to the database when this isn't necessary, as this is costly.
Model instances can be created with FactoryBoy's `build` rather than `create`
strategy if they don't need to be saved to the database. Use `bulk_create` and
FactoryBoy's `build_batch` where possible when creating multiple objects to
reduce the number of transactions required.

Tests that need to run in a transaction should use
`@pytest.mark.django_db(transaction=True)`. For example, tests that involve
constraints, database triggers, raw SQL, or multiple savepoints (such as using
the `atomic` context manager within tests).  These tests should also be marked
as `slow_test`.

Model changes and migrations that only affect the schema are implicitly tested
by `pytest-django` when it applies the migrations while building the test
database. These types of migrations don't require separate unit tests. However,
custom or hand-written migrations that perform additional tasks, such as data
changes, won't be tested implicitly because the test database is generated
empty. Such migrations should be tested manually against a recent production
dataset and possibly with `pytest` test cases.


## Tooling
We use [coverage.py](https://coverage.readthedocs.io/) to check test coverage on the code base and require 100% coverage for CI to pass.

[FactoryBoy](https://factoryboy.readthedocs.io/) provides our model factories for easy creation of model instances inside tests.

[PyTest fixtures](https://docs.pytest.org/en/latest/reference/fixtures.html) provide useful helpers for the tests.
They are also the ideal place to build up combinations of factories, eg [the `user` fixture](https://github.com/opensafely-core/job-server/blob/62a376aa120542d246efd854bc1d4de1b70a60cf/tests/conftest.py#L63-L77) which provides a User with associated Org.
We also provide Django RequestFactory's testing tools as fixtures to mirror pytest-django.

[pytest-django](https://pytest-django.readthedocs.io/en/latest/) is the bridge between pytest and Django, exposing various Django testing tools (Client, RequestFactory, etc) as fixtures.


## Verified Fakes
We use a fake object, `FakeGitHubAPI`, to test our uses of GitHub's API.
However, we want to [verify that fake](https://pythonspeed.com/articles/verified-fakes/), so we have a set of verification tests in `tests/verification/`.

`test-verification` will run those tests marked with `pytest.mark.verification`, but `just test` and `just test-ci` will not (see [ADR#21](docs/adr/0022-move-verification-tests.md) for more details).
This way, the verification tests verify our faster tests are correct.
We have a separate GitHub org, `opensafely-testing`, and bot user, `opensafely-testing-bot`, for performing these tests.
We use a different env var, `GITHUB_TOKEN_TESTING`, to pass the required PAT in.
This is a token with the same scope as [`JOBSERVER_GITHUB_TOKEN`](DEVELOPERS.md#rotating-the-read-only-github-token), but for the `opensafely-testing-bot` user.


## Useful Flows

`just test` will run most of the tests and runs quickly to provide a short feedback
loop. `just test-ci` will run the tests as CI does, however as the suite grows
this gets slower over time. One possible workflow is to run `just test`
(possibly scoped to particular areas with parameters as below) until you have
something you want to open a PR for, then run `just test-ci` to run all the
tests and coverage before pushing.

Some useful `pytest` / `just test*` parameters:

* Passing the name of a test directory, file, class, or function will only run those tests.
* `-k <partial test name>`: Run the tests matching a partial name.
* `--lf` / --`last-failed`: run the tests which failed in the last run, good for iteratively fixing tests.
* `-x`: stop at the first test failure, good for iteratively working through known broken tests.
* `--pdb`: Enter the interactive Python debugger immediately after a failure, allowing you to inspect the state at the point of error.
* `-v / --verbose`: Increase verbosity to see individual test names and results.
* `--collect-only`: Display the list of all discovered tests without running them. Useful for checking test discovery.
* `--nomigrations`: Set up the test DB directly from models instead of by applying migrations. Runs somewhat faster. Useful if migrations/models are not relevant to your changes.
* `--durations=<N>`: Show the slowest N tests and setup/teardown times. Useful when trying to speed up the test suite. Note that the initial DB setup is included against the first test run per-worker.
* `-n`: from the `pytest-xdist` plugin. Tells `pytest` how many worker processes to
  spawn. Use `-n 0` if you insert an explicit `breakpoint()` in your code, to
  stop the plugin interfering.


## Testing Releases
Releases, and their associated ReleaseFiles, are an area of the codebase where a little extra care needs to be taken.  ReleaseFiles can have on-disk files associated with them, and setting up the paths to do this requires knowledge of the parent Release as well.

To aid in testing these we have some fixtures which orchestrate pieces of the different layers for you.

Fixtures prefixed with `build_` return functions so you have some control over the output.
If you need full control then drop down to the relevant factories.

The 4 you're most likely to use are:

`build_release`
Returns a builder function which takes a list of name strings and kwargs.
A `ReleaseFile` will be created for each name you specify.
kwargs will be passed down to the `ReleaseFactory` constructor.
It returns a `Release` instance.

`build_release_with_files`
Just like `build_release` this returns a builder function with takes a list of name strings and any kwargs for `ReleaseFactory`, but also creates the files on disk for you.

`file_content`
Returns a bytes literal of random content.
This is useful when you're testing the upload of files and need content for the upload.
The other fixtures use this to generate their content.

`release`
Returns a `Release` instance with one attached `ReleaseFile` and an on-disk file with random content in it.  The `ReleaseFile`s name is `file1.txt`.
This is built on top of all the other fixtures.


There are some lower level functions which might be useful in some instances:

`build_release_path`
Generates the path for a given `Release` instance and makes sure it exists on disk.

`build_release_file`
Builds a `ReleaseFile` instance with the given name, for the given `Release` and write a file to disk.
