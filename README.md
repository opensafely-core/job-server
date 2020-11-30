# OpenSAFELY job server

This Django app provides a simple REST API which provides a channel
for communicating between low-security environments (which can request
that jobs be run) and high-security environments (where jobs are run).


## Deployment

It is currently configured to be deployed Heroku-style, and requires
the environment variables defined in `environment-sample`.

The DataLab job server is deployed to our `dokku` instance.

## Testing

A docker image for testing can be built with

    docker-compose build --build-arg pythonversion=3.8.1

The contents of `environment-sample-docker` should be edited and copied to `.env`, and a Django development server can be started with `docker-compose up`.


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
