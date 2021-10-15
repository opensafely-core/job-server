# OpenSAFELY Job Server

This is the Web UI for requesting Jobs are run within the [OpenSAFELY platform](https://opensafely.org), and viewing their logs.

It provides an API to [job-runner](https://github.com/opensafely-core/job-runner) which executes those Jobs in high-security environments.

## Stack

This is a [Django](https://www.djangoproject.com) project.
It uses [Django Rest Framework](https://www.django-rest-framework.org) for the API and [PostgreSQL](https://www.postgresql.org/) for the database.
It is deployed via [dokku](https://dokku.com), serves static files using the [whitenoise](http://whitenoise.evans.io) package, and is itself served by [gunicorn](https://gunicorn.org).
We authenticate Users with the [Python Social Auth](https://python-social-auth.readthedocs.io) Django-specific package, using [GitHub](https://github.com/) as the OAuth Provider backend.

Tests are run with [pytest](https://docs.pytest.org) and a selection of plug-ins.

We use [black](https://black.readthedocs.io) and [isort](https://pycqa.github.io/isort/) to automatically format the codebase, with [flake8](https://flake8.pycqa.org) for linting.
Each tool, including pytest, has been configured via config files, but a Makefile also exists to script common use cases (eg check and fix formatting).
[pre-commit](https://pre-commit.com) is configured to run the same checks via git hooks.

Frontend assets are managed in [Node.js](https://nodejs.org/) using [npm](https://www.npmjs.com/) and [Vite](https://vitejs.dev/).

CI is handled by [GitHub Actions](https://github.com/features/actions) where the tests and tooling are run.
After a successful merge to `main` a deployment is run.

Errors are logged to the DataLab [Sentry](https://sentry.io) account.

## Developer docs

Please see the [additional information](DEVELOPERS.md).
