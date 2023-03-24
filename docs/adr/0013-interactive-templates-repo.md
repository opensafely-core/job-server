# 13. Use external repo for interactive code schema and templates
Date: 2023-03-24

## Status
Accepted

## Context

We need to support dynamically generating code from user input as part of OSI.
Functionally, this has two main parts: 1) the form the user fills in, and 2 analysis
code templates to be rendered with the form data.

These two parts are tightly coupled - changes to the form data schema needs to
match changes in the templates.

However, whilst the form itself must live in job-server repo, there are reasons
having the templates in job-server repo is problematic:

1) job-server would need to run tests for research code, which can be slow.

2) researchers need to develop the research code using the job-server repo and
   tooling, which is likey confusing.

3) we want to move the rendering/committing of generated code out to a secure
   service in future, for security reasons.


## Decision

We will use a separate `interactive_templates` repo to hold the form data
schema and templated code, as well as the glue code to perform the rendering
and committing.  Job-server will have a pinned dependency on this repo as
a python package.


## Consequences

1. Local development of job-server and the templates are independent and
   simpler.

2. Having the schema and template code in the same repo makes it easier for
   researcher to make changes.

3. Explicit pinning means we can manage updates to the templates in job-server
   as part of the normal dependency update workflow.

4. In future, it will be simpler to move the rendering to be in a separate
   secure service. Note that when we do this, job-server will *still* need
   a dependency on `interactive_templates`, in order to use the correct form
   data schema.  But it won't perform the rendering/committing, it will POST
   the schema to the secure service.
