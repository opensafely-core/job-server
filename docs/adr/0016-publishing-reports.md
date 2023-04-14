# 16. Publishing interactive reports
Date: 2023-04-10

## Status
Accepted

## Context
As part of OSIv2 we have added reports to job-server.
Their implementation aligns with the Reports service in that they are an output from a pipeline job, rendered with some extra styles.
In this service this means they are also ForeignKey'd to the underlying ReleaseFile.

We already have a process for publishing outputs via the Snapshot models and the outputs-viewer.
However for a report the rendering of a given HTML file matters.
We also want to better model the process of a user requesting an object on our platform is made public.
We know this usually comes with some back and forth, and so backing that into the platform will help out both researchers and staff.


## Decision
We will add a flow for users to request that a given report, and the file it is created from, is made public.


## Consequences
We can provide staff a queue of requests to deal with.
Teams will be able to handle those as they see fit.

By modelling the request process, and not just the input/output states, we can track various metrics inherent to that process, for example time to decision might be useful to teams who deal with these requests.
