# OpenSAFELY Job Server
This is the Web UI for requesting Jobs are run within the [OpenSAFELY platform](https://opensafely.org), and viewing their logs.

It provides an API to [job-runner](https://github.com/opensafely-core/job-runner) which executes those Jobs in high-security environments.


## Stack
This is a [Django](https://www.djangoproject.com) project, using [Django Rest Framework](https://www.django-rest-framework.org) for the API, and [SQLite](https://www.sqlite.org/index.html) for the database.
It is deployed via [dokku](https://dokku.com), serves static files using the [whitenoise](http://whitenoise.evans.io) package, and is itself served by [gunicorn](https://gunicorn.org).
We authenticate Users with the [Python Social Auth](https://python-social-auth.readthedocs.io) Django-specific package, using [GitHub]() as the OAuth Provider backend.

Tests are run with [pytest](https://docs.pytest.org) and a selection of plug-ins.

We use [black](https://black.readthedocs.io) and [isort](https://pycqa.github.io/isort/) to automatically format the codebase, with [flake8](https://flake8.pycqa.org) for linting.
Each tool, including pytest, has been configured via config files, but a Makefile also exists to script common use cases (eg check and fix formatting).
[pre-commit](https://pre-commit.com) is configured to run the same checks via git hooks.

CI is handled by [GitHub Actions](https://github.com/features/actions) where the tests and tooling are run.
After a successful merge to `main` a deployment is run.

Errors are logged to the DataLab [Sentry](https://sentry.io) account.




## Deployment
It is currently configured to be deployed Heroku-style, and requires
the environment variables defined in `dotenv-sample`.

The DataLab job server is deployed to our `dokku2` instance.

## Deployment instructions
### Create app

```bash
dokku$ dokku apps:create job-server
dokku$ dokku domains:add job-server jobs.opensafely.org
dokku$ dokku git:set job-server deploy-branch main
```

### Create storage & load sqlite db into it

```bash
dokku$ mkdir /var/lib/dokku/data/storage/job-server
dokku$ chown dokku:dokku /var/lib/dokku/data/storage/job-server
dokku$ cp ./job-server-db.sqlite3 /var/lib/dokku/data/storage/job-server/db.sqlite3
dokku$ chown dokku:dokku /var/lib/dokku/data/storage/job-server/*
dokku$ dokku storage:mount job-server /var/lib/dokku/data/storage/job-server/:/storage
```

### Configure app

```bash
dokku config:set job-server ADMIN_USERS='xxx'
dokku config:set job-server BACKENDS='tpp,emis'
dokku config:set job-server BASE_URL='https://jobs.opensafely.org'
dokku config:set job-server DATABASE_URL='sqlite:////storage/db.sqlite3'
dokku config:set job-server EMAIL_BACKEND='anymail.backends.mailgun.EmailBackend'
dokku config:set job-server GITHUB_TOKEN='xxx'
dokku config:set job-server MAILGUN_API_KEY='xxx'
dokku config:set job-server SECRET_KEY='xxx'
dokku config:set job-server SENTRY_DSN='https://xxx@xxx.ingest.sentry.io/xxx'
dokku config:set job-server SENTRY_ENVIRONMENT='production'
dokku config:set job-server SOCIAL_AUTH_GITHUB_KEY='xxx'
dokku config:set job-server SOCIAL_AUTH_GITHUB_SECRET='xxx'
```

### Manually pushing

```bash
local$ git clone git@github.com:opensafely-core/job-server.git
local$ cd job-server
local$ git remote add dokku dokku@MYSERVER:job-server
local$ git push dokku main
```

### extras

```bash
dokku letsencrypt job-server
dokku plugin:install sentry-webhook
```

### Test Mailgun

```bash
dokku$ dokku enter job-server
container$ python manage.py sendtestemail me@myemail.org
```

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
