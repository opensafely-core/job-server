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
- [Actions](#actions)
- [Auditing events](#auditing-events)
  - [Presenters](#presenters)
- [Interfaces](#interfaces)
  - [RAP API (RAP Controller interface)](#rap-api-rap-controller-interface)
  - [Airlock interface](#airlock-interface)
- [Risky migrations](#risky-migrations)

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
- **uv**
- **Node.js v20.x** ([fnm](https://github.com/Schniz/fnm#installation) is recommended)
- **npm v7.x**
- **Postgres 17**

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
If you do not have access to pull production backups, follow the [setting up a fresh install](#setting-up-a-fresh-install) instead of restoring a backup.


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
just manage migrate
```

**Build the assets:**

See the [Compiling assets](#compiling-assets) section.

**Run the dev server:**

```sh
just run
```

Access at [localhost:8000](http://localhost:8000)

Note: the following commands require that you have a local RAP API
to connect to. See the [job-runner docs](https://github.com/opensafely-core/job-runner/blob/main/DEVELOPERS.md#running-locally-with-a-local-job-server)
for instructions on how to run job-server and the RAP controller/agent together.

**Run the rap status service:**
```sh
just run-rapstatus
```

**Run the dev server and the rap status service together:**
```sh
just run-all
```


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

[Django Staticfiles app](https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/) then collects the files and places them in the `staticfiles/assets` folder, with the manifest file located at `assets/dist/.vite/manifest.json`.

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
   just manage create_user <your_github_username> -s
   ```

1. Click on your avatar in the top right-hand corner of the site to access the Staff Area from the dropdown menu
1. First, create a Backend – you do not need to enter a Level 4 URL
1. In the User section of the Staff Area, give your user access to the new Backend
1. Then create an Organisation
1. Within your Organisation, add yourself as a Member
1. Click on Account in the header, then Applications, then start a new application
1. Once you've completed your application, go back to the Staff Area, head to the Applications and Approve your application
1. Once approved you will have a Project, add yourself to the project as a "Project Developer"
1. View your project on the site, and now you have permissions you can "Create a new workspace"

Workspace creation currently requires a link to a repo, so from this point onwards you will need to make changes directly in the database to create a workspace, and make job requests.

### Compiling requirements

The generation of `requirements*.txt` files is handled by the `_compile` `just` recipe, which uses `uv pip compile`.

### Upgrade OpenTelemetry dependencies

The opentelemetry dependencies need to be upgraded as a group. To do this, bump the relevant versions in `requirements.prod.in` and then attempt to manually resolve the dependencies by upgrading a number of packages simultaneously. A recent example of this is:

```bash
$ uv pip compile --generate-hashes --output-file requirements.prod.txt requirements.prod.in --upgrade-package opentelemetry-instrumentation --upgrade-package opentelemetry-exporter-otlp-proto-http --upgrade-package opentelemetry-sdk --upgrade-package opentelemetry-instrumentation-django --upgrade-package opentelemetry-instrumentation-psycopg2 --upgrade-package opentelemetry-instrumentation-requests --upgrade-package opentelemetry-instrumentation-wsgi --upgrade-package opentelemetry-semantic-conventions --upgrade-package opentelemetry-util-http --upgrade-package opentelemetry-instrumentation-dbapi --upgrade-package opentelemetry-api --upgrade-package opentelemetry-proto --upgrade-package opentelemetry-exporter-otlp-proto-common
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

# run Playwright functional tests
just test-functional

# watch a specific functional test in browser, slowed down
# This is useful in combination with script pausing when writing tests:
# https://playwright.dev/python/docs/api/class-page#page-pause
just test-functional <path/to/test>::<test name> --headed --slowmo=500

# debug a specific functional test
# See https://playwright.dev/python/docs/debug for more information.
PWDEBUG=1 just test-functional <path/to/test>::<test name>

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

Enter [Django's CheckConstraint constraint](https://docs.djangoproject.com/en/5.2/ref/models/constraints/#s-checkconstraint) which allows us to encode that relationship at the database level.
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


## Actions

The [jobserver.actions](jobserver/actions/) package is, by convention, the home
for code that applies create, update, or delete operations across multiple
models. Centralising this business logic reduces duplication and keeps views
focused.

Model or manager methods may perform such operations where they don't involve
complex cross-model interactions or significant side effects.

This is currently a convention, not an enforced rule. It may not be
consistently applied.

## Auditing events

We track events that we want in our audit trail with the AuditableEvent model.
It avoids foreign keys so any related model isn't blocked from being deleted.
Code that creates these should live in [jobserver.actions](jobserver/actions/),
as it always involves multiple models.

### Presenters
Since AuditableEvents have no relationships to the models they record changes in we have to manually look up those models, where we can for display in the UI.
The presenters package exists to handle all of this.
There are a few key parts to it.

AuditableEvents have a `type` field which tracks the event type they were created for.

`get_presenter()` takes an AuditableEvent instance and returns the relevant presenter function, or raises an UnknownPresenter exception.

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

Management commands might be used in other repos' tooling and CI. While not
required, it's helpful to check for downstream impacts if you change their API.

### RAP API (RAP Controller interface)

The [RAP Controller] is a component of [Job Runner] that schedules jobs requested
by users of Job Server to be run in a secure backend.

The [RAP Agent] is a component of [Job Runner] that runs in a container in a secure
backend. It runs jobs scheduled by the [RAP Controller] for its backend.

Job Server communicates with the [RAP Controller] via the [RAP API], using the [rap_api] module.
The [RAP API] is specified using the OpenAPI specification and is documented publicly.

Refer to the [Job Runner documentation] for further information on the design principles
and architecture of the RAP API, Controller and Agent.

#### Authorization

Job Server provides an Authorization token (the `RAP_API_TOKEN` environment variable)
in the header of any request to the [RAP API]. The [RAP API] uses this token to determine:

  1. that the client (Job Server) is authorised to access the API
  1.  which backends the client (Job Server) is allowed to add/modify jobs or request information about.

Refer to the [RAP API Auth] for details on how the [RAP Controller] handles client tokens.

This token was generated and configured in production for both components
ad-hoc during the initiative that created the API. We don't rotate the token.

#### Creating a job request

When users initiate a [Job Request] in the UI, Job Server calls the [RAP API] (`POST /controller/v1/rap/create/`)
to request that jobs are created for the requested actions ([JobRequest].request_job_creation).
The [RAP API] responds with a count of jobs scheduled by the controller. At this point no jobs have
yet been created on job server.

#### Updating jobs

Job Server's [RAP status service] runs in a separate container to the main Job Server web process. It
[requests updates] from the [RAP Controller] about the status of jobs for active job requests. The service calls the
[RAP API] (`GET /controller/v1/rap/status/`) in a loop (with a 60s delay between repeats, or
as configured by the `RAP_API_POLL_INTERVAL` environment variable),
and updates Job Server's `Job`s' status based on the job data returned in the RAP API response.

"Active" job requests are those that are pending or running, and also those
in an unknown status. If an initial job request creation failed with an unknown
error, this allows Job Server to request an update from the [RAP Controller] and
update the unknown status accordingly.

```mermaid
flowchart TD
    User-->JobRequest
    User-->Jobs
    JobRequest--RAP API rap/create-->RAPController
    JobRequest--RAP API rap/cancel-->RAPController
    Jobs--RAP API rap/cancel-->RAPController
    RAPStatusService--RAP API /rap/status (approximately every 60s)-->RAPController
    RAPStatusService--creates/updates-->Jobs


    subgraph JobServer
      JobRequest@{ shape: cyl }
      Jobs@{ shape: cyl }
    end

    RAPStatusService[RAP Status Service]

    RAPController{{Rap Controller}}
```

#### Backend status

A cron job calls the [RAP API] (`GET /controller/v1/backend/status/`) every 60 seconds to retrieve updates on the
status of backends, using a [management command].

(Current as of 2025-10.)

[RAP Agent]: https://github.com/opensafely-core/job-runner/agent
[RAP Controller]: https://github.com/opensafely-core/job-runner/controller
[Job Runner]: https://github.com/opensafely-core/job-runner
[RAP API]: https://controller.opensafely.org/controller/v1/docs
[RAP API Auth]: https://github.com/opensafely-core/job-runner/blob/main/controller/webapp/views/auth/rap.py
[Job Runner documentation]: https://github.com/opensafely-core/job-runner/blob/main/DEVELOPERS.md#operating-principles
[JobRequest]: jobserver/models/job_request.py
[Job Request]: jobserver/views/job_requests.py
[RAP status service]: jobserver/management/commands/rap_status_service.py
[requests updates]: jobserver/actions/rap.py
[management command]: jobserver/management/commands/rap_update_backend_status.py
[rap_api]: jobserver/rap_api.py

### Airlock interface

[Airlock] is a container that runs in a secure backend. Researchers interact
with it to view moderately sensitive outputs produced by [Job Runner], to view
log output from jobs, and to create requests to release files.  Users with the
[OutputChecker] role interact with it to review such release requests and to
manage the release of files to Job Server.

URLs are relative to the root of the
Job Server API endpoint (https://jobs.opensafely.org/api/v2 in production).

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


## Risky migrations

Be cautious when making migrations where the old code is incompatible with the
new database state. Unhandled exceptions can occur in some circustances under
our deployment strategy:

- When deploying PRs that include migrations, the old container may briefly run
against a migrated database before the new container takes over.
- If deployment fails after or while running migrations, the old container may remain active
against the modified schema.

**Safe changes** include:
- adding a model or field - the old code will not query the new fields;
- making a field nullable.

**For risky changes, split application changes from migrations into multiple PRs:**

- **Removing a model or field**
   - PR 1:
       - Remove all code references to the model/field.
       - Remove the model/field in the last commit in the PR.
       - Do **not** commit the schema migration for the removal.
       - If the field is non-nullable, make it nullable in a commit before the
         commit that removes the field.  Include the corresponding migration.
         Else, the tests may fail as the objects created by the test framework may
         not be valid according to the database schema from the migrations.
   - PR 2: Schema migration for the removal.

- **Making a field non-nullable**
   - PR 1: migration to populate any current null values and code updates to ensure the field is always set.
   - PR 2: migration and code changes to update field defintion `null=false`.

- **Renaming a model or field**
   - PR 1: add the new model or field and replicate data.
   - PR 2: update code to use the new version.
   - PR 3: migration and code changes to remove the old model or field.
