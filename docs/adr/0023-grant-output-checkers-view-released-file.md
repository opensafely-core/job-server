# 22. Grant output checkers permission to view released files

Date: 2024-08-14

## Status

Accepted

## Context

Output checkers need to view previously-released files when assessing a file requested for release in order to understand:
* [Secondary Disclosure][1] risks from combination of the requested file(s) with previous releases from this project
* The context of decisions previously made when output checking previous file versions (e.g. if previously rejected, for what reason and what may have changed since)

This need has been previously satisfied by assigning output checkers the global `ProjectCollaborator` role (per the [team manual][2]).
This further confuses the notion of what a "collaborator" role is for a project, and what/why permissions may be associated with this role.

## Decision

The `OutputChecker` role shall be granted the `release_file_view` permission.

## Consequences

Output checkers need for this permission is more explicitly defined and justified within Job Server codebase.

The potentially confusing `ProjectCollaborator` role assignments for output checkers may be removed.

[1]: https://ukdataservice.ac.uk/app/uploads/thf_datareport_aw_web.pdf "UK Data Service - Handbook on Statistical Disclosure Control for Outputs"
[2]: https://github.com/ebmdatalab/team-manual/blob/a6e1fa1d1706996893e5598a577cf0840088d131/docs/products/output-checking.md?plain=1#L155 "Bennett Institute Team Manual - Output Checking"
