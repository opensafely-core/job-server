# 2. Implement Interactive using the Django web framework

Date: 2022-04-08

## Status

Accepted

## Context

*Note: this was originally written for the standalone Interactive application and has been moved across as part of the integration into Job Server. The original ADR can be found [here](https://github.com/opensafely-core/interactive.opensafely.org/blob/main/docs/adr/0002-implement-using-the-django-web-framework.md).*

The issue motivating this decision, and any context that influences or constrains the decision.

The OpenSAFELY Interactive application needs a web based frontend for users to request analyses and to serve up the results of analyses. This is expected to have very limited requirements at first, but could become more complex in future as more options are provided for more detailed and varied analyses.

While this frontend could be appended to an existing application, like OpenCodelists or the Job Server, we don't yet know how it will grow and what features will be required in future. At the time of implementation, the Job Server requires users to have a GitHub account and we know that we don't want that as a requirement for OpenSAFELY Interactive users.

Most of the Bennett Institute applications use Django, so we have established patterns for using it and it's what the majority of the team are familar with.

## Decision

The OpenSAFELY Interactive application be standalone and will use the most recent stable version of the Django web framework.

## Consequences

There's a bit more work upfront to create the application and to host it, compared to using an existing system. However, it will be easier to maintain and expand in future, or to throw away, since this is currently an MVP.
