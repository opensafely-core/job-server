# 30. Backend status update uses runjobs cron

Date: 2025-10-23

## Status

Accepted

## Context

The job-server needs to store information about the status of the backends, so that it can be presented to end-users. As part of the RAP API phase 2 work, it will now retrieve this information from the rap-controller using a call to the RAP API. We have created a Django management command `check_rap_api_status` which gets this data from the RAP API and stores it in the database, however this command updates the data once and then exits.
We need to run this code repeatedly in order to keep the database up to date, we think that this should be once a minute.

## Decision

We have decided to use the runjobs cron system to repeatedly run the one-off management command. This system consists of:

* a set of `cron` jobs in `app.json` as per [Dokku Scheduled Cron Tasks](https://dokku.com/docs/processes/scheduled-cron-tasks/).
* the `cron` jobs in `app.json` do not define specific commands to run, instead they use the `runjobs` management command
* the `runjobs` management command is run on a number of useful standard time intervals, e.g. `hourly`, `daily`, etc
* the `runjobs` jobs are defined in subdirectories of `jobserver/jobs/` e.g. `jobserver/jobs/hourly`

In order to keep repeatedly run the `check_rap_api_status` management command, we will create a `runjobs` job in `jobserver/jobs/minutely/check_rap_api_status.py`.

## Consequences

* We did not have 'minutely' as a frequency for `runjobs` jobs, we have added it as part of this work.
* Dokku will run the job on schedule every minute. At the time of writing the job typically takes about 140ms to run, and we do not expect that to change significantly. In the unlikely event that it took longer than a minute to run, it's possible we could have two jobs running simultaneously and conflicting.
