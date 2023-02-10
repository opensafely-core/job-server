# 7. Retain database backup for 90 days

Date: 2023-02-08

## Status

Accepted

## Context

The database for job-server is currently stored on a managed cluster which is able to keep daily backups for seven days. A recent regression in the codebase caused some database fields to be truncated, and was not spotted until about six days after deployment. In this case, we were able to repair the truncated data using an old backup, but if it had gone a little bit longer without being spotted we would have experienced minor data loss.

Our current opinion is that although seven days is sufficiently long enough to spot recover in the event of catastrophic dataloss, we should keep backups for longer to help recover from more subtle dataloss/degradation.

## Decision

In addition to the seven-day backups provided by our database cluster, we will use an external service to retain backups of the jobserver database for a longer period. The backup will be generated daily, and we will keep the last 90 days of backups.

## Consequences

We will have a much bigger window to spot & recover from any data degradation issues. The daily backup file is currently ~39MB, which implies a total backup history of around 3.33GB. This will easily fit within current cloud storage allowance, and would only cost around $0.06/mo at current prices if we exceed our allowance.
