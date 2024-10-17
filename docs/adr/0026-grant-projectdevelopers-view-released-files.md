# 24. Grant Project Developers permission to view released files

Date: 2024-09-25

## Status

Accepted

## Context

There are two roles that are assigned at project level to researchers working on a project: `ProjectDeveloper` and `ProjectCollaborator`.

`ProjectCollaborator` can

- view outputs that have been released to Job Server.
  `ProjectDeveloper` can
- Run and cancel jobs.
- Manage a project (edit project metadata).
- Create and manage workspaces.
- View unreleased outputs on Level 4 and request their release.
- Request that released outputs are published.

Any person assigned the `ProjectDeveloper` role will have been deemed a bona fide researcher who has signed the required agreements to view unreleased outputs.

Viewing of released outputs, which have undergone the output checking process, requires fewer such checks on the person in question and is made available to collaborators on a project who might not necessarily be the primary researchers.
Thus, the `ProjectCollaborator` is sometimes assigned to people who are not assigned the `ProjectDeveloper` role.

Persons assigned the `ProjectDeveloper` role also need to view released outputs and so are routinely also assigned the
`ProjectCollaborator` role. This has caused confusion (see [#4519](https://github.com/opensafely-core/job-server/issues/4519)) and we cannot see a good reason why this permission is omitted from the `ProjectDeveloper` role.

## Decision

The "view released outputs" permission (`release_file_view`) shall be granted to the `ProjectDeveloper` role.

## Consequences

The Bennett Team Manual will need to be updated to remove recommendations to assign both of these roles to research users.

The Bennett Information Governance Team will need to be made aware of this change.

There will remain now-redundant assignments of both `ProjectDeveloper` and `ProjectCollaborator` in the Job Server database until these are rectified.
