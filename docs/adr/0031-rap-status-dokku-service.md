# 31. Rap status update uses Dokku service

Date: 2025-10-23

## Status

Accepted

## Context

The job-server needs to store information about the status of every job, so that it can be presented to end-users. Until now, a sync loop in rap-controller would regularly post this information to the job-server's jobs API. As part of the RAP API phase 2 work, job-server will now retrieve this information from the rap-controller using a call to the RAP API. We have created a function `jobserver/commands/rap.py::rap_status_update()` which gets this data from the RAP API and stores it in the database.

## Decision

We have decided to use a long-running update process, with Dokku providing a second container in which to run it.

The long-running update process will be a new management command `rap_status_service`, consisting of a loop which updates the job statuses and then sleeps for 60 seconds.

The second Dokku container and associated configuration is defined in `Procfile` & `app.json`. We have disabled zero-downtime deploys for the second container in order to prevent Dokku from running two containers simultaneously.

Although we have initially decided to update the data approximately every minute, we decided not to use the runjobs cron system because the runtime of this update is variable based on the size of job_requests. At the time of writing, the runtime could plausibly be over a minute in a realistic scenario, which would mean we would need to guard against multiple updates running simultaneously.

## Consequences

The new container will be re-deployed automatically as part of the existing deployment mechanism every time there is an update to job-server.
