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
