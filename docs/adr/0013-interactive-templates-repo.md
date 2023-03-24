# 13. Use external repo for interactive code schema and templates
Date: 2023-03-24

## Status
Accepted

## Context

We need to support dynamically generated code from user input as part of OSI.
Functionally, this has two main parts: 1) the form the user fills in, and 2) analysis
code templates to be rendered with the form data.

These two parts are tightly coupled - changes to the form data schema needs to
match changes in the templates.

However, whilst the form itself [must live in job-server
repo](0005-migrate-interactive-into-job-server.md), there are reasons that make
having the templates there problematic:

1) job-server would need to run tests for research code, which can be slow.

2) researchers need to develop the research code using the job-server repo and
   tooling, which is likey confusing.

3) we want to move the rendering/committing of generated code out to a secure
   service in future, for security reasons.


## Decision

We will use a separate [interactive-templates
repo](https://github.com/opensafely-core/interactive-templates) to hold the
templated code, and a form data schema, as well as the glue code to perform the
rendering and committing.

Job-server will have a pinned dependency on this repo as a python package, and
use the schema and glue code and bundled templates to generate OSI commits.


## Consequences

1. Local development of job-server and the templates are independent and
   simpler.

2. Having the schema and template code in the same repo makes it easier for
   researcher to make changes.

3. Explicit pinning means we can manage updates to the templates in job-server
   as part of the normal dependency update workflow. This does mean that making
   a change to tempaltes for form data schema means committing it to
   interactive-templates and then bumping the dependency. While slightly
   onerous, this ensures we have robust synchronisation between job-server and
   interactive-templates. i.e. committing to interactive-templates won't break
   job-server.

4. In future, it will be simpler to move the rendering to be in a separate
   secure service. Note that when we do this, job-server will *still* need
   a dependency on `interactive_templates`, in order to use the correct form
   data schema.  But it won't perform the rendering/committing, it will POST
   the schema to the secure service.
