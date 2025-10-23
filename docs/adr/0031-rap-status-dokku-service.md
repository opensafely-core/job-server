# 31. Rap status update uses Dokku service

Date: 2025-10-23

## Status

Accepted

## Context

The `job-server` needs to store information about the status of every job, so that it can be presented to end-users. Until now, a sync loop in `rap-controller` would regularly post this information to the job-server's jobs API. As part of the RAP API phase 2 work, `job-server` will now retrieve this information from the `rap-controller` using a call to the RAP API. We have created a Django management command `rap_status` which gets this data from the RAP API and stores it in the database.

## Decision

We have decided to use a long-running update process, with Dokku providing a second container in which to run it.

The long-running update process will be a new management command `rap_status_service`, consisting of a loop which updates the job statuses and then sleeps for 60 seconds.

The second Dokku container and associated configuration is defined in `Procfile` & `app.json`.

## Consequences

The new container will be re-deployed automatically as part of the existing deployment mechanism every time there is an update to `job-server`. When Dokku deploys containers it creates the new container, switches over to the new container, waits 60 seconds, then kills the old container. This means that it's possible for two different containers to be running simultaneously.
