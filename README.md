# OpenSAFELY Job Server
This is the Web UI for requesting Jobs are run within the [OpenSAFELY platform](https://opensafely.org), and viewing their logs.

It provides an API to [job-runner](https://github.com/opensafely-core/job-runner) which executes those Jobs in high-security environments.


## Stack
This is a [Django](https://www.djangoproject.com) project.
It uses [Django Rest Framework](https://www.django-rest-framework.org) for the API and [SQLite](https://www.sqlite.org/index.html) for the database.
It is deployed via [dokku](https://dokku.com), serves static files using the [whitenoise](http://whitenoise.evans.io) package, and is itself served by [gunicorn](https://gunicorn.org).
We authenticate Users with the [Python Social Auth](https://python-social-auth.readthedocs.io) Django-specific package, using [GitHub]() as the OAuth Provider backend.

Tests are run with [pytest](https://docs.pytest.org) and a selection of plug-ins.

We use [black](https://black.readthedocs.io) and [isort](https://pycqa.github.io/isort/) to automatically format the codebase, with [flake8](https://flake8.pycqa.org) for linting.
Each tool, including pytest, has been configured via config files, but a Makefile also exists to script common use cases (eg check and fix formatting).
[pre-commit](https://pre-commit.com) is configured to run the same checks via git hooks.

CI is handled by [GitHub Actions](https://github.com/features/actions) where the tests and tooling are run.
After a successful merge to `main` a deployment is run.

Errors are logged to the DataLab [Sentry](https://sentry.io) account.


## Local Development Set Up
### Native
Create a virtualenv with your preferred tool and install the dependencies with:

    pip install -r requirements.txt


Run migrations:

    python manage.py migrate


Set up the environment variables listed in `dotenv-sample` with your tool of choice.


Optionally set up 1 or more administrators by setting `ADMIN_USERS` to a list of strings.
eg `ADMIN_USERS=ghickman,ingelsp`.

**Note:** this can only contain usernames which exist in the database.

Then update their User records with:

    python manage.py ensure_admins


Run the dev server:

    python manage.py runserver


### Docker Compose
Copy `dotenv-sample` to `.env` and run `docker-compose up`.

*Note:* The dev server inside the container does not currently reload when changes are saved.


## Deployment
It is currently configured to be deployed Heroku-style, and requires
the environment variables defined in `dotenv-sample`.

The DataLab job server is deployed to our `dokku2` instance, instructions are are in [INSTALL.md](INSTALL.md).


## Testing

Run `make dev-config` if you have not already. Note: you will need the
bitwarden cli tool installed in order to access passwords.

A Django development server can be started with `docker-compose up`.


### V2
To test the integration of job-runner and job-server follow these steps:

#### Initial Run
1. Run job-server locally
1. Log in
1. Go to http://localhost:8000/workspaces/new and create a workspace
1. Create a workspace
1. Create a `JobRequest` via the actions list on the Workspace page
1. Configure job-runner to point at your local job-server
1. Run job-runner with `rm -f workdir/db.sqlite && python -m jobrunner.sync`

#### Subsequent Runs
1. Run this against the job-server database: `update jobserver_job set status_code = NULL, status_message = '', started = false, started_at = NULL, completed_at = NULL;` (this will wipe all local Job state)
1. Run job-runner with `rm -f workdir/db.sqlite && python -m jobrunner.sync`


## Add/Updating Static Assets
We don't currently use any kind of static asset management tool (eg npm, yarn,
etc) for this project.

Each static asset has been downloaded from the appropriate site and added to
the project with their version number.

To add or update an asset:

1. Download the asset from its respective site (with `wget` or your favourite tool)
1. Move the production version to `static/<location>/`
1. Rename to include the version number (eg `bootstrap.min.css` -> `bootstrap-4.5.0.min.css`)


## Adding New Backends

### Steps
1. Add an empty migration with `python manage.py makemigrations jobserver --empty --name <meaningful name>`.
1. Create your Backend(s) in a function via RunPython in the new migration file.
1. Fix the tests (some will check the number of migrations).

### Why
Backends in this project represent a [job runner](https://github.com/opensafely-core/job-runner) instance somewhere.
They are a Django model with a unique authentication token attached.

We generate them with a migration, but configure which ones are available to a deployment with the `BACKENDS` environment variable.

This has allowed us some benefits:
* API requests can be tied directly to a Backend (eg get all JobRequests for TPP).
* Adding a new Backend via environment variables allows for easy local testing.
* Per-Backend API stats collection is trivial because requests are tied to a Backend via auth.

However it comes with sticky parts too:
* You need to create them via migration _and_ enable them via the environment.
* The tests are inherently tied to the number of Backends because we want to test the default manager filters them by the names configured in the environment variable.
