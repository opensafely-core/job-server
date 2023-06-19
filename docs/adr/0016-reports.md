# 16. Reports
Date: 2023-06-16

## Status
Accepted

## Context
An OSIv2 analysis produces reports, so as part of moving OSI into job-server we need to also support reports here.


## Decision
We will support reports in job-server by mirroring the implementation of those in the Reports service, with the exception that the underlying ReleaseFile is related to a Report via a ForeignKey.

We are defining a Report on the OpenSAFELY platform as:

    A released file wrapped with some extra metadata and styling.


Reports are expected to define certain HTML classes which job-server will use to style them.


## Consequences
We expect portions, if not the whole Reports service to be merged into job-server at a future date.
By defining what a report is here, with those reports hosted on the Reports service in mind, we hope to ease that transition.
