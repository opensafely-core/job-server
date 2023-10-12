# 17. Auditing events
Date: 2023-10-12

## Status
Accepted

## Context
We have various actions throughout the system that we would like to keep track of in an audit log.
We can piece some of these actions together by inferring state from various database records, but would like a system that captures them, and displays them to interested parties as necessary.

There are several packages out there that will providing auditing for us, but we could not find any that suited our needs.


## Decision
We will build a system for auditing arbitrary events in the system.


## Consequences
We will add an auditing model, with code to create and view those records.
