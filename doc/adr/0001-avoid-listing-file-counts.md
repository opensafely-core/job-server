# 1. Avoid listing file counts unless user is authenticated

Date: 2022-03-21

## Status

Accepted

## Context

A request was made to include the number of files on one of the buttons in the release list view.

See discussion for ticket [#1660](https://github.com/opensafely-core/job-server/issues/1660)

## Decision

The number of files is only to be made available for authenticated users and not for members of the public.

## Consequences

Someone who is not logged in will not have access to the files and does not need to see the number of files in a release. This creates a cleaner user experience, while avoiding the disclosure of any unnecessary information.

The additional information could potentially provide avenues of attack. However, the attack mechanism is unclear. These files have been output checked and will be released in the future, so risk is likely to be small. This decision could be reviewed in the future if additional requirements appear.
