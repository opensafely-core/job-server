# Developer documentation

- [Local development](#local-development)
  - [Native](#native)
    - [Prerequisites](#prerequisites)
    - [Steps](#steps)
  - [Docker Compose](#docker-compose)
- [Deployment](#deployment)
- [Testing](#testing)
- [Adding or updating static assets](#adding-or-updating-static-assets)
- [Adding new backends](#adding-new-backends)
  - [Steps to add a backend](#steps-to-add-a-backend)
  - [Why add a backend?](#why-add-a-backend)

## Local development

### Native

#### Prerequisites

- **Python v3.9.x**
- **virtualenv**
- **Pip**
- **Node.js v16.x** ([fnm](https://github.com/Schniz/fnm#installation) is recommended)
- **npm v7.x**

#### Steps

**Create a virtualenv with your preferred tool and install the dependencies with:**

```sh
make setup
```

**Set up environment:**

_Note:_ you will need the [Bitwarden CLI tool](https://bitwarden.com/help/article/cli/) installed in order to access passwords.

```sh
make dev-config
```

Alternatively, for limited functionality without requiring access to special passwords, copy `dotenv-sample` to `.env`,
or export the environment variables in `dotenv-sample` with your tool of choice.

**Run migrations:**

```sh
python manage.py migrate
```

Optionally set up 1 or more administrators by setting `ADMIN_USERS` to a list of strings.
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

```sh
npm run build
```

**Run the dev server:**

```sh
make run
```

Access at [localhost:8000](http://localhost:8000)

### Docker Compose

Set up environment as above:

```sh
make dev-config
```

Run `docker-compose up`.

_Note:_ The dev server inside the container does not currently reload when changes are saved.

## Deployment

It is currently configured to be deployed Heroku-style, and requires the environment variables defined in `dotenv-sample`.

The DataLab job server is deployed to our `dokku2` instance, instructions are are in [INSTALL.md](INSTALL.md).

## Testing

Run `make dev-config` if you have not already.

_Note:_ you will need the [Bitwarden CLI tool](https://bitwarden.com/help/article/cli/) installed in order to access passwords.

Run the tests with:

```sh
make test
```

## Adding or updating static assets

We don't currently use any kind of static asset management tool (eg npm, yarn, etc) for this project.

Each static asset has been downloaded from the appropriate site and added to the project with their version number.

To add or update an asset:

1. Download the asset from its respective site (with `wget` or your favourite tool)
2. Move the production version to `static/<location>/`
3. Rename to include the version number (eg `bootstrap.min.css` -> `bootstrap-4.5.0.min.css`)

## Adding new backends

### Steps to add a backend

1. Add an empty migration with `python manage.py makemigrations jobserver --empty --name <meaningful name>`.
2. Create your Backend(s) in a function via RunPython in the new migration file.
3. Fix the tests (some will check the number of migrations).

### Why add a backend?

Backends in this project represent a [job runner](https://github.com/opensafely-core/job-runner) instance somewhere.
They are a Django model with a unique authentication token attached.

We generate them with a migration, but configure which ones are available to a deployment with the `BACKENDS` environment variable.

This has allowed us some benefits:

- API requests can be tied directly to a Backend (eg get all JobRequests for TPP).
- Adding a new Backend via environment variables allows for easy local testing.
- Per-Backend API stats collection is trivial because requests are tied to a Backend via auth.

However it comes with sticky parts too:

- You need to create them via migration _and_ enable them via the environment.
- The tests are inherently tied to the number of Backends because we want to test the default manager filters them by the names configured in the environment variable.
