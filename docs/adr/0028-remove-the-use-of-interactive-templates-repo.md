# 28. Remove use of external repository for interactive code schema and templates

Date: 2025-02-27

## Status

Accepted

## Context

In [ADR 13](0013-interactive-templates-repo.md), we specified the use of
an external repository to handle templated code for OpenSAFELY
Interactive.

We are now removing the OpenSAFELY Interactive functionality.

## Decision

Since the use of the functionality is no longer required, we can remove
the use of the external repository, and archive that repository.

## Consequences

1. [ADR 13](0013-interactive-templates-repo.md) no longer applies.
2. We no longer have this dependency in job-server.
3. We no longer need to maintain the external repository.
