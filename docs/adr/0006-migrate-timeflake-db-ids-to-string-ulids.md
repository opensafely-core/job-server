# 6. Use string ULID for Analysis Request DB ids

Date: 2023-01-25

## Status

Accepted

## Context

Timeflake uses a uuid column type in Postgres, and validates that any value passed to the field is a valid timeflake, raising a ValidationError when it can't parse the given value.

This breaks queries which pass an invalid timeflake, such as:

* `Model.objects.filter(pk="invalid timeflake")`
* `Model.objects.get(pk="invalid timeflake")`

In practice this meant wrapping nearly all query call sites with try/except logic to make them behave in more expected ways.

We tried modifying the library to pass given values directly to the db but since the field was implemented with a uuid column type this raised an error, exposed as a DataError in Django.

While this behaviour mirrors that of similar fields, such as Django's own UUIDField, it created a lot of friction while working with the column.  Common operations like testing or looking up an invalid page required extra work to support.


## Decision

We will mirror how ReleaseFile.id works, using a CharField with `jobserver.models.common.new_ulid_str` as the default value generator.


## Consequences

This will make the implementation of our two ULID fields consistent, giving developers less to reason about when using them.

Both fields make use of the python-ulid library, but because we're storing the values in a CharField we're not tied to that library if we need to change in the future.
