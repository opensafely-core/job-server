# 10. Creating Interactive queries v2
Date: 2022-04-14

## Status
Accepted

## Context
In ADR-0003 we defined how OSIv1 would write a new commit for each AnalysisRequest.

For v2 users will fill in an application for the kinds of study they want to run with the interactive tool.
This means we will have one project per interactive application to match how the rest of the platform functions.
As such we can't use the same workspace for all interactive requests.

## Decision
Projects will have one interactive workspace for the v2 iteration of interactive (see ADR-0008 for how we will reference them).
While we expect this to change the future we're going to stick to one for ease of development in this iteration.
This also means we will have a single "interactive" repository on GitHub _per project_.

We will keep the rest of the submission semantics the same as v1 (defined in ADR-0003) because all the benefits still apply.

## Consequences
The consequences for continuing with this way of submitting code will match those in ADR-0003.
