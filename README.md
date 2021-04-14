# OpenSAFELY Job Server
This is the Web UI for requesting Jobs are run within the [OpenSAFELY platform](https://opensafely.org), and viewing their logs.

It provides an API to [job-runner](https://github.com/opensafely-core/job-runner) which executes those Jobs in high-security environments.




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
