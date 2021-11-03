# Job server deployment instructions
## Create app

```bash
dokku$ dokku apps:create job-server
dokku$ dokku domains:add job-server jobs.opensafely.org
dokku$ dokku git:set job-server deploy-branch main
```

## Configure app

```bash
dokku config:set job-server ADMIN_USERS='xxx'
dokku config:set job-server BASE_URL='https://jobs.opensafely.org'
dokku config:set job-server DATABASE_URL='postgres://localhost/jobserver'
dokku config:set job-server EMAIL_BACKEND='anymail.backends.mailgun.EmailBackend'
dokku config:set job-server GITHUB_TOKEN='xxx'
dokku config:set job-server MAILGUN_API_KEY='xxx'
dokku config:set job-server SECRET_KEY='xxx'
dokku config:set job-server SENTRY_DSN='https://xxx@xxx.ingest.sentry.io/xxx'
dokku config:set job-server SENTRY_ENVIRONMENT='production'
dokku config:set job-server SOCIAL_AUTH_GITHUB_KEY='xxx'
dokku config:set job-server SOCIAL_AUTH_GITHUB_SECRET='xxx'
```

## Manually pushing

```bash
local$ git clone git@github.com:opensafely-core/job-server.git
local$ cd job-server
local$ git remote add dokku dokku@MYSERVER:job-server
local$ git push dokku main
```

## extras

```bash
dokku letsencrypt job-server
dokku plugin:install sentry-webhook
```

## Ensure persistent logs
```bash
dokku$ sudo mkdir -p /var/log/journal
```

## Test Mailgun

```bash
dokku$ dokku enter job-server
container$ python manage.py sendtestemail me@myemail.org
```
