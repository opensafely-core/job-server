# 23. Replace Global Project Developer with Deployment Administrator Role

Date: 2024-08-19

## Status

Accepted

## Context

The `ProjectDeveloper` role has historically been assignable both to a `ProjectMembership` (i.e. "this user is a developer on this project") and to a `User`, which effectively grants said user the `ProjectDeveloper` permissions globally across all projects.

There is a lack of semantic consistency in a role name containing the word "project" with the fact the role it identifies can be used to grant global (rather than project-scoped) permissions.
The permissions associated with the `ProjectDeveloper` role are wide ranging and are liable to raise questions as to the appropriateness of global assignment of these.

Investigation revealed only members of Bennett Institute staff had been assigned this role, and after discussion amongst the Tech Group it was deemed that this was likely to facilitate Technical Support activities (primarily job management on behalf of researcher users).
In instances of system unavailability, it may be preferable to re-run jobs on behalf of users rather than asking the user to perform this themselves for reasons of expediency and user ease.
Whilst individual jobs can be re-run via `job-runner` this presents the following issues:

- deletion of logs from the previous attempted run
- re-use of job identifiers
- we can only rerun individual jobs from job-runner. If a job fails, its dependencies are then cancelled. This can be quite inconvenient in the case of large job requests.

The OpenSAFELY Developer Permissions Log states that a Platform Developer can only run jobs in any project if they have the Deployment Administrator role.
If the user providing technical support has this role, then they may perform these tasks themselves; if they do not then they should delegate to a user who does.

## Decision

We will create a new role for users performing tech support tasks that require the Deployment Administrator role and is explicitly named as such, and has only the permissions allowed in the Developer Permissions Log for this role.
At the time of writing this will solely be the ability to run and cancel jobs.

We will reassign users with the "global" `ProjectDeveloper` role this new Deployment Administrator role.

We will remove the ability to assign the `ProjectDeveloper` role to `User` model objects.

## Consequences

There will be greater clarity as to the purpose of roles within the system and the reasons for their assignment.

Certain tech support activities that were previously possible with the `ProjectDeveloper` role may not be possible with the new Deployment Administrator role.
Some these may have been better served by the user performing the activity themselves under guidance, others may be indicative of a need to modify the permissions associated with this role.
We will monitor this internally through the Tech Group.
