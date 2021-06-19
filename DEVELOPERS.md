# Local Development Set Up
## Native

Prerequisites:
- **Python v3.9.x**
- **virtualenv**
- **Pip**

Create a virtualenv with your preferred tool and install the dependencies with:

    make setup

Set up environment (note: you will need the bitwarden cli tool installed in order to access passwords):

    make dev-config

Alternatively, for limited functionality without requiring access to special passwords, copy `dotenv-sample` to `.env`,
or export the environment variables in `dotenv-sample` with your tool of choice.

Run migrations:

    python manage.py migrate

Optionally set up 1 or more administrators by setting `ADMIN_USERS` to a list of strings.
eg `ADMIN_USERS=ghickman,ingelsp`.

**Note:** this can only contain usernames which exist in the database.
If necessary, you can create the required user(s) first with:

    python manage.py createsuperuser

Then update their User records with:

    python manage.py ensure_admins

Run the dev server:

    make run

Access at http://localhost:8000

## Docker Compose

Set up environment as above:

    make dev-config

Run `docker-compose up`.

*Note:* The dev server inside the container does not currently reload when changes are saved.


# Deployment
It is currently configured to be deployed Heroku-style, and requires
the environment variables defined in `dotenv-sample`.

The DataLab job server is deployed to our `dokku2` instance, instructions are are in [INSTALL.md](INSTALL.md).

# Testing

Run `make dev-config` if you have not already. Note: you will need the
bitwarden cli tool installed in order to access passwords.

Run the tests with:

    make test

# Add/Updating Static Assets
We don't currently use any kind of static asset management tool (eg npm, yarn,
etc) for this project.

Each static asset has been downloaded from the appropriate site and added to
the project with their version number.

To add or update an asset:

1. Download the asset from its respective site (with `wget` or your favourite tool)
2. Move the production version to `static/<location>/`
3. Rename to include the version number (eg `bootstrap.min.css` -> `bootstrap-4.5.0.min.css`)

# Adding New Backends

## Steps
1. Add an empty migration with `python manage.py makemigrations jobserver --empty --name <meaningful name>`.
2. Create your Backend(s) in a function via RunPython in the new migration file.
3. Fix the tests (some will check the number of migrations).

## Why
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
