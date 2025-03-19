# 29. Sunset OpenSAFELY Interactive

Date: 2025-03

## Status

Accepted.

## Context

OpenSAFELY Interactive (OSI) was a Job Server app allowing users to request
simple analyses.  We are removing OSI.

Refer to the Team Manual for more information:

- [wiki](https://bennett.wiki/products/opensafely-interactive/)
- [source permalink](https://github.com/ebmdatalab/team-manual/blob/51426e9d25457b6f61d0de12aaebad34f736a054/docs/products/opensafely-interactive.md?plain=1#L1)

## Decision

We will securely archive OpenSAFELY Interactive outputs.

We will remove all data and code relating to OpenSafely Interactive from the
site.

## Consequences

- All ADR relating to OSI are deprecated.
- Users will not be able to use OSI.
- We will remove the following models/functionality and related data and code:
  - `interactive.AnalysisRequest`, the main model representing an OSI request;
  - `jobserver.Report` and `jobserver.ReportPublishRequest`, the models representing OSI outputs. These are written generically but have no other clients and we don't plan to use them in future;
  - OSI login form;
  - OSI-related `User` properties and code;
  - OSI-related permissions/roles;
  - OSI-related parts of the Jobs/Releases APIs;
  - the OSI React app.
- We will remove any infrastructure and tooling relating to OSI.
- We will remove any dependencies that are unused following the above changes.

Refer to the `initiative:sunset-osi` label in Job Server tickets to find changes made:
https://github.com/opensafely-core/job-server/issues?q=label%3A%22initiative%3Asunset-osi%22%20
