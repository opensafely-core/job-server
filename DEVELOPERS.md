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
  - [Data Setup](#data-setup)
  - [Upgrade OpenTelemetry dependencies](#pip-opentelemetry)
- [Deployment](#deployment)
- [Testing](#testing)
  - [Slack Testing](#slack-testing)
- [`django-upgrade`](#django-upgrade)
- [Components](#components)
- [Backends](#backends)
- [Rotating the GitHub token](#rotating-the-github-token)
- [Interactive testing](#interactive-testing)
- [Dumping co-pilot reporting data](#dumping-copilot-reporting-data)
- [Ensuring paired field state with CheckConstraints](#ensuring-paired-field-state-with-checkconstraint)
  - [Common patterns](#common-patterns)
- [Auditing events](#auditing-events)
  - [Presenters](#presenters)

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

Optionally give 1 or more administrators access to the Staff Area by setting `ADMIN_USERS` to a list of strings.
For example: `ADMIN_USERS=ghickman,ingelsp`.

_Note:_ this can only contain usernames which exist in the database.
If necessary, you can create the required user(s) first with:

```sh
python manage.py createsuperuser
```

Then update their User records with:

```sh
python manage.py ensure_admins
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

For styling this project uses [Tailwind CSS](https://tailwindcss.com/), and then [PostCSS](https://github.com/postcss/postcss) for post-processing.

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

### Data Setup
Sometimes it's useful to have a fresh local installation or you may not have authorization to download a production backup.
In that situation you can follow the steps below to set up your local copy of the site:

1. Create [a GitHub OAuth application](https://github.com/settings/applications/new).
   * The callback URL must be `http://localhost:8000/complete/github/`.
   * The other fields don't matter too much for local development.
1. Register a user account on your local version of job-server by clicking Login
1. Set the `SOCIAL_AUTH_GITHUB_KEY` (aka "Client ID") and `SOCIAL_AUTH_GITHUB_SECRET` environment variables with values from that OAuth application.
1. Give your user the `CoreDeveloper` role by:
   * Setting the `ADMIN_USERS` environment variable to include your username.
   * Running `python manage.py ensure_admins`.
1. Click on your avatar in the top right-hand corner of the site to access the Staff Area.
1. Create an Org, Project, and Backend in the Staff Area.
1. On your User page in the Staff Area link it to the Backend and Org you created.
1. Assign your user account to the Project with `ProjectDeveloper` and `ProjectCollaborator` roles on the Project page within the Staff Area.
1. Navigate to the Project page in the main site using the "View on Site" button.
1. Create a Workspace for the Project.
1. Create a JobRequest in the Workspace.

If you need one or more Jobs linked to the JobRequest you will need to create them in the database or with the Django shell.

### pip-opentelemetry

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

### Slack Testing

With a valid bot token, you can run tests and have any slack messages generated
actually sent to a test channel by setting some environment variables:

```
export SLACK_BOT_TOKEN=...
export SLACK_TEST_CHANNEL=job-server-testing
just test-dev
```


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

### Rotating the OSI GitHub token
1. Log into the `opensafely-interactive-bot` GitHub account (credentials are in Bitwarden).
1. Got to the [opensafely-interactive-token](https://github.com/settings/tokens/1005632984).
1. Click "Regenerate token".
1. Set the expiry to 90 days.
1. Copy the new token.
1. ssh into `dokku4.ebmdatalab.net`
1. Run: `dokku config:set job-server INTERACTIVE_GITHUB_TOKEN=<the new token>`


## Interactive Testing
Job Server uses the interactive-templates repo code, imported as a Python package, to run OS Interactive analyses and to generate reports.

To facilitate local testing, the `osi_run` Django management command has been created to produce a report from an Analysis Request. It's used like this:

`python manage.py osi_run <analysis-request-slug>`

The resulting HTML report is output into the `workspaces` directory and can be released, so that it's visible within Job Server, using the `osi_release` management command:

`python manage.py osi_release <analysis-request-slug> <user-name> --report workspaces/<analysis-request-pk>/report.html`

These two actions can be combined using the `osi_run_and_release` management command:

`python manage.py osi_run_and_release <analysis-request-slug> <user-name>`

Alternatively, the `osi_release` command can be used without running an analysis first, for fast development, using a fake report:

`python manage.py osi_release <analysis-request-slug> <user-name>`

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
                check=(
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
                check=Q(updated_at__isnull=False, updated_by__isnull=False),
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
