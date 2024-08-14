# 21. Move verification testing to its own GitHub workflow

Date: 2024-08-12

## Status

Accepted

## Context

Regular CI runs (on push, PR etc.) ran all tests, including the verification tests.
We use verification tests to ensure that our understanding of external APIs is still correct and that our fake API objects, used in our unit tests, are still valid.
These verification tests make requests to the GitHub API (and the OpenCodelists API).

Lots of CI runs in close succession results in this API returning 403 errors (see #4434),  causing test failures.
Concurrent CI workflow runs (e.g. when two developers push to different PRs at the same time) can also cause test failures due to them sharing state in the opensafely-testing GitHub org.

## Decision

Verification tests will be moved to their own GitHub workflow, which will be run on its own nightly schedule.

## Consequences

The frequency of requests made to the GitHub API by job server tests will be reduced, which should reduce the frequency of test failures caused by 403 errors from the API.

Verification tests will be run less frequently, it is possible that a PR could be merged to main without having had verification tests run against it.

Our deployment pipeline will no longer be dependent on the availability of the GitHub or OpenCodelists API.
