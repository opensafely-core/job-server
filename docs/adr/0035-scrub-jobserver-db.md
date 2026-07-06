# 35. Scrubbed copy of JobServer database for local development

Date: 2026-07-06

## Status

Accepted

Supersedes [ADR 32](0032-pii-scrub-jobserver-db.md).

## Context

For local development, developers commonly pull down a copy of the JobServer production database and work with it. We use a script to hourly dump the production database to Dokku4 so people can easily access it. This process has many advantages, like developers working against realistic data, and testing database changes against the "real" data, which is more likely to pick up errors than synthetic data.

But the trade-offs have become uncomfortable. We end up storing identifiable/sensitive data on Dokku4, and on developer machines, and because the restored DB looks almost identical to production, it’s easy to forget which instance you’re in.

## Decision

We will keep the workflow of restoring a production-like database for local development, but the routinely available dump will be scrubbed before developers use it.

We will replace the existing hourly raw database dump with a daily scrubbed dump. An hourly dump is not necessary for local development because most development/debugging work does not depend on data being updated hourly. Running the dump hourly also increases load on the source database. A daily scrubbed dump is a better default balance between usefulness, operational load, and data protection.

If a raw production dump is required for a specific task, it can still be generated manually using `dump_raw_data` management command. That use should be exceptional. Before copying personal data, developers should follow the [personal data copying policy](https://bennett.wiki/tech-group/policies/personal-data-copying-policy/#personal-data-copying-policy) and discuss the plan with their line manager or Tech SLT.

We will create a separate `jobserver_data_scrubbing` database in the same DigitalOcean PostgreSQL cluster as the `jobserver` production database. We will also create a dedicated `jobserver_data_scrubbing` database user for this workflow.

The `jobserver_data_scrubbing` user is intentionally restricted:

- it has read access to the production `jobserver` database, including existing and future tables and sequences, so it can create dumps;
- it owns the `jobserver_data_scrubbing` database, so it can restore, modify, scrub, and clear data there.

The scheduled job will:

1. Create a raw dump from the readonly replica of the JobServer database, using the restricted `jobserver_data_scrubbing` database user.
2. Restore that dump into the separate `jobserver_data_scrubbing` database.
3. Run the `scrub_data` management command against the `jobserver_data_scrubbing` database.
4. Create a scrubbed dump from the `jobserver_data_scrubbing` database.
5. Clear the `jobserver_data_scrubbing` database after the job runs.

The `scrub_data` command uses model-level `DataScrubbing` configuration to decide which fields are scrubbed and which fields are explicitly allowed to keep their real values. It also truncates selected Django and social-auth tables that may contain sessions, tokens, or personal data that is not needed in a development database.

We will add integration tests to ensure every field on scrubbed models is explicitly categorised as either scrubbed or allowed. These tests should fail when a model field is added, removed, or renamed without updating the corresponding `DataScrubbing` configuration.

Some values are intentionally not scrubbed because they are already publicly available or are needed for the development database to remain useful. These exceptions are documented in [this doc](https://docs.google.com/document/d/1dEo2fiGOgkyBw1Gk-9RrobRKL-i44jQa-BQcWOeBBbI/edit?usp=sharing).

## Consequences

We significantly reduce the risk of personal data leakage when developers pull down a copy of the database, as the scrubbed dump will not contain real emails, tokens, or other sensitive fields.

Developers still benefit from realistic data shapes and row counts, which means local testing and schema changes are less likely to diverge from production.
