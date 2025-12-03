# 32. PII scrubbed copy of Job Server database

Date: 2025-12-03

## Status

Accepted

## Context

For local development, developers commonly pull down a copy of the Job Server production database and work with it. We use a script to hourly dump the production database to dokku 4 so people can easily access it. This process has many advantages, like developers working against realistic data, and testing database changes against the "real" data, which is more likely to pick up errors than synthetic data.

But the trade-offs have become uncomfortable. We end up storing identifiable/sensitive data on Dokku 4, and on developer machines, and because the restored DB looks almost identical to production, it’s easy to forget which instance you’re in.

## Decision

We will keep this workflow of restoring a prod-like database, but we’ll generate that copy in a way that strips out all sensitive information. Instead of the old hourly dumps, we will now run a daily job, thus reducing load on the source database. This job will build a temporary clone of the database schema and populate it with safe data, using an allow list to determine which columns retain real values and substituting convincing fakes everywhere else. It will then dump that scrubbed copy to dokku 4 and scratch the temporary schema afterwards.

Developers can then restore this sanitised dump just like the old one, so they still see realistic tables and row counts, but no real emails, passwords, or tokens ever leave production. The only maintenance requirement is keeping the allowlist in sync with the models: when we add a column that requires real values locally, we add it to the allowlist; otherwise, the sanitiser will automatically fill it with fake data.

## Consequences

We significantly reduce the risk of personal data leakage when developers pull down a copy of the database, as the sanitised dump will not contain real emails, tokens, or other sensitive fields.

Developers still benefit from realistic data shapes and row counts, which means local testing and schema changes are less likely to diverge from production.
