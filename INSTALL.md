# Job server deployment instructions
## Create app

```bash
dokku$ dokku apps:create job-server
dokku$ dokku domains:add job-server jobs.opensafely.org
dokku$ dokku git:set job-server deploy-branch main
```

## Configure app

```bash
dokku config:set job-server BASE_URL='https://jobs.opensafely.org'
dokku config:set job-server CSP_REPORT_URI='xxx'
dokku config:set job-server DATABASE_URL='postgres://localhost/jobserver'
dokku config:set job-server EMAIL_BACKEND='anymail.backends.mailgun.EmailBackend'
dokku config:set job-server JOBSERVER_GITHUB_TOKEN='xxx'
dokku config:set job-server MAILGUN_API_KEY='xxx'
dokku config:set job-server OTEL_EXPORTER_OTLP_ENDPOINT='https://api.honeycomb.io'
dokku config:set job-server OTEL_EXPORTER_OTLP_HEADERS='x-honeycomb-team=xxx,x-honeycomb-dataset=job-server'
# disabling some instrumentations may be necessary depending on honeycomb quota
dokku config:set job-server OTEL_PYTHON_DISABLED_INSTRUMENTATIONS='psycopg2'
dokku config:set job-server OTEL_SERVICE_NAME='job-server'
dokku config:set job-server SECRET_KEY='xxx'
dokku config:set job-server SENTRY_DSN='https://xxx@xxx.ingest.sentry.io/xxx'
dokku config:set job-server SENTRY_ENVIRONMENT='production'
dokku config:set job-server SOCIAL_AUTH_GITHUB_KEY='xxx'
dokku config:set job-server SOCIAL_AUTH_GITHUB_SECRET='xxx'

# Disable zero-downtime deploys for the rapstatus process (which runs the rap_status_service
# manangement command). We don't ever want two of these loops running simultaneously
dokku checks:disable job-server rapstatus
```


## Manually deploying from a docker image

Manually deploy from a locally built docker image in the same way that we do in CI.

```bash
# build prod image, tag with a custom version and push
local$ just docker/build prod
local$ docker tag job-server ghcr.io/opensafely-core/job-server:job-server-manual-deploy
local$ docker push ghcr.io/opensafely-core/job-server:job-server-manual-deploy
# Find the image name and sha
local$ docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/opensafely-core/job-server:job-server-manual-deploy
```

Deploy:
```bash
dokku$ dokku git:from-image job-server <image name/sha>
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

## View logs

You can view logs through dokku:

```bash
# web container
dokku logs job-server
# rapstatus container
dokku logs -p rapstatus job-server
```

Or directly in journalctl:

```bash
sudo journalctl -t job-server
```

## Test Mailgun

```bash
dokku$ dokku enter job-server
container$ python manage.py sendtestemail me@myemail.org
```

## Rotating the Django secret key

If this is a *routine rotation* of the secret key
— and not a compromised secret key —
you can temporarily leave the secret key to be rotated alongside the new secret key.

This allows for changing the secret key without logging out all users at once.

There are three steps to this process.

### 1. Duplicate the existing secret key

```bash
dokku config:set job-server OLD_SECRET_KEY="$(dokku config:get job-server SECRET_KEY)"
```

### 2. Replace the existing secret key

```bash
# Prefix the command with a space to avoid saving the input to shell history:
 dokku config:set job-server SECRET_KEY='xxx'
```

You can generate a new secret key as follows:

```py
from django.core.management.utils import get_random_secret_key

get_random_secret_key()
```

### 3. Remove the previous secret key

A suitable expiry time is given by adding the `SESSION_COOKIE_AGE` duration
to the time at which the secret key was replaced.
Once that expiry time is reached,
any sessions created before the secret key was replaced will have then expired anyway.

If this is not set in the code,
Django's default [`SESSION_COOKIE_AGE`](https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-age) is *two weeks*.

Set a Slack reminder for this time,
and then remove `OLD_SECRET_KEY` as soon as possible when reminded:

```bash
dokku config:unset job-server OLD_SECRET_KEY
```
