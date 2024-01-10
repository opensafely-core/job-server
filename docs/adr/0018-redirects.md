# 18. Publishing interactive reports
Date: 2023-04-10

## Status
Accepted

## Context
After identifying that Organisations should be able to collaborate on Projects, the first task was to remove Organisation slugs from the root of all relevant URLs.  To do so would affect the vast majority of URLs in the system, so we looked at ways to do redirects, knowing that we would likely need to do this for more than Projects in the long term.


## Decision
We will create a Redirect model with mutually exclusive ForeignKeys to expected "target" models, `Org`, `Project`, and `Workspace` to start with.  We will make use of Django's CheckConstraints to add the mutual exclusive part of this design, and we will track various metadata such as creator, updator, deletor, etc on the model.

We make use of these Redirect objects via a middleware to match the start of a request's URL to the old URL stored on any objects, and redirect the request to relevant object's `get_absolute_url`.

While Django does ship with `django.contrib.redirects.Redirect` it was missing various properties we were keen to make use of, eg who created or deleted a redirect, and is tied to the sites framework which requires we teach the application about where it's deployed.


## Consequences
We will be able to remove Orgs from the top level of the URL structure.

We can create redirects for `Org`, `Project`, and `Workspace` models, and it will be possible to add more models as we identify the need.

Redirects will be handled for all models below a target in the model hierarchy, eg moving a Workspace from one project to another will create a redirect that triggers for any related JobRequest, Job, etc.

Staff users will be able to move instances of certain models in the staff area, and the relevant View will create the necessary Redirect instance under the hood.

Any further data tidy up work we need to do will now benefit from unbroken URLs.
