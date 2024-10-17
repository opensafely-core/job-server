# 25. Renaming or Deleting Role Classes

Date: 2024-10-10

## Status

Accepted

## Context

`jobserver.authorization.roles` contains a number of "role" classes.

These are used to assign sets of `permission`s to `User` or `ProjectMembership` instances.

These assignments are stored in the database in a `jobserver.authorization.fields.RolesArrayField`, which is an array of `RoleField`.
The corresponding database type for this field is an array of strings, and the values of these strings are the "dotted paths" of the
role classes, as produced by `dotted_path(cls)`.

These role path strings are turned back into their corresponding role classes by `jobserver.authorization.parsing.parse_roles(paths)`.

Certain types of modification of a role class (renaming, deleting) can result in the situation where there are role paths in the database
that no longer correspond to role classes in the codebase. In this situation, `parse_roles` will raise an `ImportError`.

These `ImportError`s will bubble up to HTTP 500 errors as seen following the merge of #4636, which led to the reversion of this PR.

Any data migrations that alter role assignments also depend on the role classes to which they refer.

Experiments have been conducted into resolving these dependency and `ImportError` issues via fake role classes in data migrations and
dynamic class creation were deemed to result in unacceptable complexity.

## Decision

When removing or renaming role classes we will leave a vestige of the old role class.

This vestigial role class will have no permissions or models associated with it.

This vestigial role class will be removed when all migrations depending on it are removed.

This vestigial role class will be marked as such in the codebase, with a corresponding indication that it should not be used.

## Consequences

The presence of role class paths in an `RolesArrayField` in the database without corresponding classes in the codebase will continue to cause HTTP 500 errors.
This situation is one which violates data integrity and so we accept the presence of these errors as a means of notifying us of this situation.

There will be vestigial classes in the `jobserver.roles.authorization` module for so long as they have references - we should ensure their removal when all references are removed.

The absence of permissions associated with a vestigial role class means that it will not meaningfully influence what permissions a user has within Job Server.

The absence of models associated with a vestigial role class means that it will not appear in either the `User` or `ProjectMembership` role edit pages.
