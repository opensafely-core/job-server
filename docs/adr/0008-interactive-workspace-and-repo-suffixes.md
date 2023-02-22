# 8. Interactive Workspace and Repo suffixes
Date: 2023-02-22


## Status
Accepted


## Context
Interactive studies fit into our general platform system in that they exist a project under which workspaces, jobs, etc all exist.
However, we want an easy way to differentiate between an Interactive workspace and "traditional" workspaces so our code knows where to create JobRequests when a user completes the Interactive form.
From the platform's perspective these are identical, we don't for instance treat them differently in job-runner.
At the time of building OSIv2 we believe that only one Interactive workspace will exist for a project because each new study will generate a new application, and thus a project.


## Decision
We will treat the Interactive workspaces as a form of singleton under a project.
We accept that this will very possibly change in the future, at which point we will need to undo this choice, but we don't expect any downsides to doing that.

To reference Interactive workspaces we will use the project slug, with `-interactive` as a suffix.

Repo objects, and the repo on GitHub, are created by staff users in the staff area when setting up an Interactive user.
Since a repo is inherently tied to a workspace it makes sense to mirror the naming scheme for workspaces to repos as well.


## Consequences
The Project model has grown some convenience properties to make it easy to get both the Interactive slug and workspace for a given project.
