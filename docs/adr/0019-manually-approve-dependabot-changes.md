# 19. Manually approve Dependabot PRs

Date: 2024-02-26

## Status

Accepted

## Context

We use Dependabot to help us keep our dependencies up to date. However, we've recently learned that auto-merging Dependabot PRs doesn't trigger a deployment. This has the potential to cause issues and led us to review our use of Dependabot.

## Decision

Configure Dependabot to raise PRs weekly for Python and NPM. Review them manually, following a process that's been agreed within the team.

## Consequences

We will need to manually review Dependabot PRs. This is what we've agreed to consider when doing the reviews:

1. The review of a Dependabot PR is not expected to be an exhaustive check and it’s not expected that the reviewer will do a code review on the upstream changes. It is reasonable to rely on automated tests to give confidence that the updates won’t introduce any breaking changes.
1. The review of a Dependabot PR may include reviewing the release notes/change log for any incompatible or significant changes that might require further testing or any suspicious/unexpected changes. However, this is optional and expected to be reserved for major version updates of important dependencies (like Python/Django).

We could revisit this decision if we satisfy ourselves that there's an automated alternative that's secure.

We may write our own replacement to Dependabot if we find the configuration options for Dependabot don't suit our needs and we find ourselves having to review too many dependencies too frequently. However, we believe for the moment that we won't have too many PRs and that figuring out a manual process for reviewing them is the more tricky step.

There's more information about this decision in this [document](https://docs.google.com/document/d/1OIyb5pCqFjvI-g6Q2-m9fGFuj32Liknq1WEsPj-MY58/edit).
