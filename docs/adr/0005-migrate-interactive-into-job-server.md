# 1. Migrate Interactive into Job Server

Date: 2023-01-17

## Status

Accepted

## Context

*Note: this was originally written for the standalone Interactive application and has been moved across as part of the integration into Job Server. The original ADR can be found [here](https://github.com/opensafely-core/interactive.opensafely.org/blob/main/docs/adr/0005-migrate-into-job-server.md).*

The initial development work on OpenSAFELY Interactive demonstrated that the idea worked and was worth investing more time in. We are now developing version 2 of OpenSAFELY Interactive, which will allow users to build up a much richer query and produce a more detailed report. We now expect to be making some ongoing changes to the report and expect to maintain OpenSAFELY Interactive for the foreseeable future.

In addition, there will be a formal application process to complete before users are able to access OpenSAFELY Interactive. This also requires that Analysis Requests are grouped into projects, which are then linked to applications.

## Decision

We will move the user-facing parts of OpenSAFELY Interactive into Job Server.

## Consequences

The recording and management of OpenSAFELY projects and organisations is done in one place and won't be duplicated for OpenSAFELY Interactive.

User management of (almost) all OpenSAFELY users is done in one place, although with two separate workflows for the time-being.

It's possible to create a much easier workflow for generating reports from the Analysis Requests. Reports will be stored alongside outputs on Job Server rather than being in a separate location.

We will no longer need to maintain two separate Django projects.

No need to maintain an API for creating JobRequests, as these will be done directly from Job Server.

However, we do add some additional complexity into Job Server; it has another responsibility and a set of users who authenticate differently (via email+password) to our existing users. We think these tradeoffs are worth it though.
