# 4. Use timeflake for Analysis Request DB ids

Date: 2022-05-04

## Status

Accepted

## Context

*Note: this was originally written for the standalone Interactive application and has been moved across as part of the integration into Job Server. The original ADR can be found [here](https://github.com/opensafely-core/interactive.opensafely.org/blob/main/docs/adr/0004-use-timeflake-db-ids.md).*

Django's default integer ids are problematic. They are insecure, and can limit scalability. See https://bennettoxford.slack.com/archives/C63UXGB8E/p1651572496402679 for more discussion on this.

Instead, we want to use ULIDs, which are loosely ordered random ids which avoid these problems, but preserve the ordering properties for good performance.

There are a number of python implementations of this concept:

 - https://pypi.org/project/python-ulid/
 - https://pypi.org/project/ulid-py/
 - https://pypi.org/project/timeflake/

They all implement the ULID concept, in slightly different ways.


## Decision

*Use timeflake to generate IDs*


Of the three timeflake has the following useful benefits over the other options:

1. Implemented as a subclass of `uuid.UUID` so that it inter-operates with them
2. Explicit django ORM support, using PostgreSQL's `uuid` column for storage.
3. Slightly less predictable, at the cost of some slightly looser ordering for IDs created in the same millisecond


## Consequences


Possible issues:

1. Timeflake is newer (~2 years old), possibly less mature.
