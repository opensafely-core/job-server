# OpenSAFELY Job Server
This is the Web UI for requesting Jobs are run within the [OpenSAFELY platform](https://opensafely.org), and viewing their logs.

It provides an API to [job-runner](https://github.com/opensafely-core/job-runner) which executes those Jobs in high-security environments.




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
