# Developer documentation

- [Local development](#local-development)
  - [Development credentials](#development-credentials)
  - [Native](#native)
    - [Prerequisites](#prerequisites)
    - [`just` commands](#just-commands)
    - [Postgres](#postgres)
      - [Installing on macOS](#installing-on-macos)
      - [Installing on Linux](#installing-on-linux)
      - [Creating a database](#creating-a-database)
    - [Restoring Backups](#restoring-backups)
    - [Steps](#steps)
  - [Docker Compose](#docker-compose)
  - [Frontend development (CSS/JS)](#frontend-development-cssjs)
  - [Running the local asset server](#running-the-local-asset-server)
  - [Compiling assets](#compiling-assets)
  - [Setting up a fresh install](#setting-up-a-fresh-install)
  - [Upgrade OpenTelemetry dependencies](#upgrade-opentelemetry-dependencies)
- [Deployment](#deployment)
- [Testing](#testing)
  - [Slack Testing](#slack-testing)
- [`django-upgrade`](#django-upgrade)
- [Components](#components)
- [Icons](#icons)
- [Backends](#backends)
- [Rotating the read only GitHub token](#rotating-the-read-only-github-token)
- [Dumping co-pilot reporting data](#dumping-co-pilot-reporting-data)
- [Ensuring paired field state with CheckConstraints](#ensuring-paired-field-state-with-checkconstraints)
  - [Common patterns](#common-patterns)
    - [Both set or null](#both-set-or-null)
    - [updated\_at and updated\_by](#updated_at-and-updated_by)
- [Auditing events](#auditing-events)
  - [Presenters](#presenters)
- [Interfaces](#interfaces)
  - [Job Runner interface](#job-runner-interface)
  - [Airlock interface](#airlock-interface)
- [Migrations deployment strategy](#migrations-deployment-strategy)

## Local development

### Development credentials

_Note:_ you will need the [Bitwarden CLI tool](https://bitwarden.com/help/article/cli/) installed in order to access passwords, but it is not a requirement.

- Create a `.env` file; there is an existing `dotenv-sample` template that you can use to base your own `.env` file on.
- Use `bw` to login to the Bitwarden account.
- When logged in to Bitwarden, run `scripts/dev-env.sh .env` to retrieve and write the credentials to the target environment file specified.
  - `.env` is already in `.gitignore` to help prevent an accidental
    commit of credentials.

### Native

#### Prerequisites

- **Python v3.12.x**
- **virtualenv**
- **Pip**
- **Node.js v20.x** ([fnm](https://github.com/Schniz/fnm#installation) is recommended)
- **npm v7.x**
- **Postgres**

#### `just` commands

Each `just` command sets up a dev environment as part of running it.
If you want to maintain your own virtualenv make sure you have activated it before running a `just` command and it will be used instead.


#### Postgres

Recommend: using docker to provide postgresql

```sh
just docker/db

```

Double check your .env has the right config to talk to this docker instance:

```
DATABASE_URL=postgres://user:pass@localhost:6543/jobserver
```


Alternatively, you can install and configure postgresql natively for your OS following the instructions below.

##### Installing on macOS

[Postgres.app](https://postgresapp.com/) is the easiest way to run Postgres on macOS, you can install it from homebrew (casks) with:

```sh
brew install --cask postgres-unofficial
```

You will need to add its bin directory to your path for the CLI tools to work.

Postico is a popular GUI for Postgres:

```sh
brew install --cask postico
```


##### Installing on Linux

Install postgresql with your package manager of choice.

[This guide](http://meshy.co.uk/posts/postgresql-without-passwords) explains how to set up ident (password-less) auth, and set some options for faster, but more dangerous, performance.

If you need to upgrade an installation the [ArchWiki](https://wiki.archlinux.org/title/PostgreSQL#Upgrading_PostgreSQL) is a good reference.


##### Creating a database

You'll need a database in Postgres to work with, run:

```sh
psql -c "CREATE DATABASE jobserver"
```

On Linux, you'll also need to create the user with relevant permissions:
```
psql -c "
CREATE ROLE jobsuser PASSWORD 'pass' NOSUPERUSER CREATEDB;
GRANT ALL PRIVILEGES on database jobserver to jobsuser;
"
```


#### Restoring Backups

Copies of production can be restored to a local database using a dump pulled from production.
If you do not have access to pull production backups, follow the [data setup section](#data-setup) instead of restoring a backup.


Backups can be copied with:

```sh
scp dokku4:/var/lib/dokku/data/storage/job-server/jobserver.dump jobserver.dump
```


If using the provided docker db you just need to do (note this will wipe your current
dev db):

```sh
just docker/restore-db jobserver.dump
```

If using a manual install, you can restore with:


```sh
pg_restore --clean --if-exists --no-acl --no-owner -d jobserver jobserver.dump
```

Note: This assumes ident auth (the default in Postgres.app) is set up.

Note: `pg_restore` will throw errors in various scenarios, which can often be ignored.
The important line to check for (typically at the very end) is `errors ignored on restore: N`.
Where `N` should match the number of errors you got.



#### Steps


**Set up an environment**

```sh
just devenv
```

**Run migrations:**

```sh
python manage.py migrate
```

**Build the assets:**

See the [Compiling assets](#compiling-assets) section.

**Run the dev server:**

```sh
just run
```

Access at [localhost:8000](http://localhost:8000)

### Docker Compose

Run `just docker-serve`.

_Note:_ The dev server inside the container does not currently rebuild the frontend assets when changes to them are made.

### Frontend development (CSS/JS)

This project uses [Vite](https://vitejs.dev/), a modern build tool and development server, to build the frontend assets.
Vite integrates into the Django project using the [django-vite](https://github.com/MrBin99/django-vite) package.

Vite works by compiling JavaScript files, and outputs a manifest file, the JavaScript files, and any included assets such as stylesheets or images.

For styling this project uses [Tailwind CSS](https://tailwindcss.com/).

### Running the local asset server

Vite has a built-in development server which will serve the assets and reload them on save.

To run the development server:

1. Update the `.env` file to `ASSETS_DEV_MODE=True`
2. Run `just assets-run`

This will start the Vite dev server at [localhost:5173](http://localhost:5173/) and inject the relevant scripts into the Django templates.

### Compiling assets

To view the compiled assets:

1. Update the `.env` file to `ASSETS_DEV_MODE=False`
2. Run `just assets-rebuild`

Vite builds the assets and outputs them to the `assets/dist` folder.

[Django Staticfiles app](https://docs.djangoproject.com/en/3.2/ref/contrib/staticfiles/) then collects the files and places them in the `staticfiles/assets` folder, with the manifest file located at `assets/dist/.vite/manifest.json`.

### Setting up a fresh install

Sometimes it's useful to have a fresh local installation or you may not have authorization to download a production backup.
In that situation you can follow the steps below to set up your local copy of the site:

1. Create [a GitHub OAuth application](https://github.com/settings/applications/new).
   - The callback URL must be `http://localhost:8000/complete/github/`.
   - The other fields don't matter too much for local development.
1. Set the `SOCIAL_AUTH_GITHUB_KEY` (aka "Client ID") and `SOCIAL_AUTH_GITHUB_SECRET` environment variables with values from that OAuth application
1. Register a user account on your local version of job-server by logging in to your local site
1. Once you have created an account, give your user the `StaffAreaAdministrator` role by running:

   ```sh
   python manage.py create_user <your_github_username> -s
   ```

1. Click on your avatar in the top right-hand corner of the site to access the Staff Area from the dropdown menu
1. First, create a Backend – you do not need to enter a Level 4 URL
1. Then create an Organisation
1. Within your Organisation, add yourself as a Member
1. Click on Account in the header, then Applications, then start a new application
1. Once you've completed your application, go back to the Staff Area, head to the Applications and Approve your application
1. Once approved you will have a Project, add yourself to the project as a "Project Developer"
1. View your project on the site, and now you have permissions you can "Create a new workspace"

Workspace creation currently requires a link to a repo, so from this point onwards you will need to make changes directly in the database to create a workspace, and make job requests.


### Upgrade OpenTelemetry dependencies

The opentelemetry dependencies need to be upgraded as a group. To do this, bump the relevant versions in `requirements.prod.in` and then attempt to manually resolve the dependencies by upgrading a number of packages simultaneously. A recent example of this is:

```bash
$ pip-compile --resolver=backtracking --allow-unsafe --generate-hashes --strip-extras --output-file=requirements.prod.txt requirements.prod.in --upgrade-package opentelemetry-instrumentation --upgrade-package opentelemetry-exporter-otlp-proto-http --upgrade-package opentelemetry-sdk --upgrade-package opentelemetry-instrumentation-django --upgrade-package opentelemetry-instrumentation-psycopg2 --upgrade-package opentelemetry-instrumentation-requests --upgrade-package opentelemetry-instrumentation-wsgi --upgrade-package opentelemetry-semantic-conventions --upgrade-package opentelemetry-util-http --upgrade-package opentelemetry-instrumentation-dbapi --upgrade-package opentelemetry-api --upgrade-package opentelemetry-proto --upgrade-package opentelemetry-exporter-otlp-proto-common
```


## Deployment

It is currently configured to be deployed Heroku-style, and requires the environment variables defined in `dotenv-sample`.

The Bennett Institute job server is deployed to our `dokku4` instance, instructions are are in [INSTALL.md](INSTALL.md).

## Testing

Run the unit tests:

```sh
just test
```

Run all of the tests (including slow tests) apart from verification tests (that hit external APIs) and run coverage, as it's done in CI:

```sh
just test-ci
```

More details on testing can be found in [TESTING.md](TESTING.md).

### Slack Testing

With a valid bot token, you can run tests and have any slack messages generated
actually sent to a test channel by setting some environment variables:

```
export SLACK_BOT_TOKEN=...
export SLACK_TEST_CHANNEL=job-server-testing
just test-dev
```

## `django-upgrade`

[`django-upgrade`](https://github.com/adamchainz/django-upgrade) is used
to migrate Django code from older versions to the current version in use.

`django-upgrade` is run via `just django-upgrade`.

`django-upgrade` also gets run via `just check`
and is also runs via the `pre-commit` checks.

When upgrading to a new Django minor or major version:

* Ensure `django-upgrade` has been run,
  and any changes `django-upgrade` makes committed.
* Update the Django version used for the invocation of `django-upgrade`
  in the `django-upgrade` recipe in the `justfile`.


## Components

Job Server uses the Slippers library to build reusable components.

To view the existing components, and see what attributes they receive, [visit the UI gallery](https://jobs.opensafely.org/ui-components/).


## Icons

Job Server uses [Hero Icons](https://heroicons.com/).

To add a new icon:
1. Find the icon you need
1. Copy the SVG to a new file in `templates/_icons/`.  The website will give you the SVG code rather than a file.
1. Edit the properties of that file so that:
  * `height` and `width` attributes should match the values in the `viewBox`
  * the class is configurable: `class="{{ class }}"`
  * `fill` should be `currentColor` unless it's an outline icon then it should be `none` and `stroke` should be `currentColor`
1. Map the icon file path to a name in `templates/components.yaml`


## Backends

Backends in this project represent a [job runner](https://github.com/opensafely-core/job-runner) instance somewhere.
They are a Django model with a unique authentication token attached.

This has allowed us some benefits:

- API requests can be tied directly to a Backend (eg get all JobRequests for TPP).
- Per-Backend API stats collection is trivial because requests are tied to a Backend via auth.


## Rotating the read only GitHub token
1. Log into the `opensafely-readonly` GitHub account (credentials are in Bitwarden).
1. Got to the [Personal access tokens (classic) page](https://github.com/settings/tokens).
1. Click on `job-server-api-token`.
1. Click "Regenerate token".
1. Set the expiry to 90 days.
1. Copy the new token.
1. ssh into `dokku4.ebmdatalab.net`
1. Run: `dokku config:set job-server JOBSERVER_GITHUB_TOKEN=<the new token>`


## Dumping co-pilot reporting data
Co-pilots [have a report](https://github.com/ebmdatalab/copiloting/tree/copiloting-report) they run every few months, building on data from this service.

To produce a dump in the format they need you will need to install [db-to-sqlite](https://pypi.org/project/db-to-sqlite/) via pip, pipx, or your installer of choice.
You will also need to set the `DATABASE_URL` environment variable.

Then run `just dump-co-pilot-reporting-data`.

## Ensuring paired field state with CheckConstraints
We have various paired fields in our database models.
These are often, but not limited to fields which track _who_ performed an action and _when_ they performed it.
It's useful to be able to ensure these related fields are in the correct state.

Enter [Django's CheckConstraint constraint](https://docs.djangoproject.com/en/4.1/ref/models/constraints/#s-checkconstraint) which allows us to encode that relationship at the database level.
We can set these in a model's Meta and use a `Q` object for the check kwarg.
See the common patterns section below for some examples.

### Common patterns
#### Both set or null
This example shows how you can ensure both fields are set **or** null.
This is our most common usage at the time of writing.

With some fields that look like this:

    frobbed_at = models.DateTimeField(null=True)
    frobbed_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.CASCADE,
        related_name="my_model_fobbed",
        null=True
    )


Your CheckConstraint which covers both states looks like this:

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        frobbed_at__isnull=True,
                        frobbed_by__isnull=True,
                    )
                    | (
                        Q(
                            frobbed_at__isnull=False,
                            frobbed_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_frobbed_at_and_frobbed_by_set",
            ),
        ]


You can then test these constraints like so:

    def test_mymodel_constraints_frobbed_at_and_frobbed_by_both_set():
        MyModelFactory(frobbed_at=timezone.now(), frobbed_by=UserFactory())


    def test_mymodel_constraints_frobbed_at_and_frobbed_by_neither_set():
        MyModelFactory(frobbed_at=None, frobbed_by=None)


    @pytest.mark.django_db(transaction=True)
    def test_mymodel_constraints_missing_frobbed_at_or_frobbed_by():
        with pytest.raises(IntegrityError):
            MyModelFactory(frobbed_at=None, frobbed_by=UserFactory())

        with pytest.raises(IntegrityError):
            MyModelFactory(frobbed_at=timezone.now(), frobbed_by=None)


#### updated_at and updated_by
This is very similar to the pattern above, except we use `auto_now=True` and don't allow nulls in the fields, which means we don't have to account for nulls in the constraint:

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        related_name="my_model_updated",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(updated_at__isnull=False, updated_by__isnull=False),
                name="%(app_label)s_%(class)s_both_updated_at_and_updated_by_set",
            ),
        ]


The use of `auto_now` also changes how we test this constraint.
It cannot be overridden when using any part of the ORM which touches `save()` because it's set there.
So we lean on `update()` instead:

    def test_mymodel_constraints_updated_at_and_updated_by_both_set():
        MyModelFactory(updated_by=UserFactory())


    @pytest.mark.django_db(transaction=True)
    def test_mymodel_constraints_missing_updated_at_or_updated_by():
        with pytest.raises(IntegrityError):
            MyModelFactory(updated_by=None)

        with pytest.raises(IntegrityError):
            mymodel = MyModelFactory(updated_by=UserFactory())

            # use update to work around auto_now always firing on save()
            MyModel.objects.filter(pk=mymodel.pk).update(updated_at=None)


## Auditing events
We track events that we want in our audit trail with the AuditableEvent model.
It avoids foreign keys so any related model isn't blocked from being deleted

As such constructing these models can be a little onerous, so we have started wrapping the triggering event, eg adding a user to a project, with a function that does both that and sets up the AuditableEvent instance.
These are currently called commands because naming things is hard, and they will, we hope, be better organised in the near future into a domain layer.
In the meantime, it's just useful to know that creating AuditableEvent instances _can_ be easier.

### Presenters
Since AuditableEvents have no relationships to the models they record changes in we have to manually look up those models, where we can for display in the UI.
The presenters package exists to handle all of this.
There are a few key parts to it.

AuditableEvents have a `type` field which tracks the event type they were created for.

get_presenter() takes an AuditableEvent instance and returns the relevant presenter function, or raises an UnknownPresenter exception.

Presenter functions take an AuditableEvent instance and trust that the caller is passing in one relevant to that function.

At the time of writing we only display events in the staff area so there is no
way to change how presenters build their context, or what template they choose.
We're aware that we might want to display them as a general feed on the site.
If this turns out to be the case the author's expectation is that we will use
inversion of control so the calling view can decide the context in which
presenters are used.
This will most likely affect the template used for each event, and where each
object links to, if anywhere.

## Interfaces

Descriptions of interfaces between this repo or container and others. These
interfaces can be changed, through coordination with the relevant teams.

Except where mentioned otherwise, URLs are relative to the root of the
Job Server API endpoint (https://jobs.opensafely.org/api/v2 in production).

Management commands might be used in other repos' tooling and CI. While not
required, it's helpful to check for downstream impacts if you change their API.

### Job Runner interface

[Job Runner] is a container that runs in a secure backend. It executes
[JobRequest]s initiated by users of Job Server.

This interacts with [jobserver/api/jobs.py] It uses the `JobRequestAPIList`
endpoint (`GET /job-requests/`) for reading `JobRequest`s. It uses the
`JobAPIUpdate` endpoint (`POST /jobs/`) for updating the `Job` table.
(Current as of 2024-09.)

 Refer to the documentation of [jobrunner.sync] for Job Runner's documentation
 of this interface.

[Job Runner]: https://github.com/opensafely-core/job-runner
[jobrunner.sync]: https://github.com/opensafely-core/job-runner/blob/main/DEVELOPERS.md#jobrunnersync
[JobRequest]: jobserver/models/job_request.py
[jobserver/api/jobs.py]: jobserver/api/jobs.py

### Airlock interface

[Airlock] is a container that runs in a secure backend. Researchers interact
with it to view moderately sensitive outputs produced by [Job Runner], to view
log output from jobs, and to create requests to release files.  Users with the
[OutputChecker] role interact with it to review such release requests and to
manage the release of files to Job Server.

Airlock refers to Job Server's permissions model to determine what users can
do. The code it needs is in [jobserver/api/releases.py]. The endpoints it uses
are `Level4TokenAuthenticationAPI` (`GET /releases/authenticate/`) and
`Level4AuthorisationAPI` (`GET /releases/authorise/`). It receives the results
of `build_level4_user` to determine whether a user is an [OutputChecker], and
which workspaces they can access. (Current as of 2024-09.)

When releases are approved, Airlock triggers creation of a [Release] for the
associated [Workspace] on Job Server through the [jobserver/api/releases.py]
`ReleaseWorkspaceAPI` endpoint (`POST /releases/workspace/{workspace_name}`).
Files are uploaded from Airlock to Job Server through the `ReleaseAPI`endpoint
(`POST releases/release/{release_id}`). (Current as of 2024-09.)

Notifications of events related to release requests are triggered through the
[airlock_event_view] endpoint (`POST /airlock/events/`), which is currently the
only responsibility of the [airlock app] within Job Server.  Depending on the
event, users are notified by email, Slack or by creating/updating GitHub
issues. (Current as of 2024-09.)

[Airlock]: https://github.com/opensafely-core/airlock
[OutputChecker]: jobserver/authorization/roles.py
[jobserver/api/releases.py]: jobserver/api/releases.py
[Release]: jobserver/models/release.py
[Workspace]: jobserver/models/workspace.py
[airlock_event_view]: airlock/views.py
[airlock app]: airlock/


## Migrations deployment strategy

When deploying PRs that include migrations, there's a brief period where the
old container may execute against a database that has been migrated, before
cutting over to the new container. Additionally, migrations may execute during
a deployment that ultimately fails, leaving the old container running. Either
scenario can result in unhandled exceptions if the old container is
incompatible with the migrated database.

Django allows for model-database inconsistencies, raising database-layer errors
only when actual issues arise. Certain changes, like adding a table or column,
are generally safe because the old code won’t query the new fields. Similarly,
making a field nullable is safe -- it won't cause database access failures and
impacts application code only if non-null values are required.

Problems arise when a table or column is removed and old code tries to access
it, or when a field is made non-nullable and old code attempts to insert null
values. For these cases, a safer deployment strategy is to split changes into
multiple PRs. First, deploy the application changes in one PR. Then, deploy the
migration in a separate PR. This approach ensures that during the migration PR
deployment, the old container is compatible with both the pre- and
post-migration database states, mitigating risks if the deployment or migration
fails.

Renaming a table or column is more complex. A good approach is to use three
PRs: first, a PR with models and migrations to create the new table or column
and replicate existing data; then a PR updating the application code to use the
new table/column; and finally, a PR to remove the old field or model and the
corresponding migration.
