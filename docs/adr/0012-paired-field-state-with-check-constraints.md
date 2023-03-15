# 12. Ensuring paired field state with CheckConstraints
Date: 2023-03-14

## Status
Accepted

## Context
We have fields on many of our database models which are inherently related.
The vast majority of these track *who* did something and *when* they did it.
We want to ensure the state of these fields stays in sync without having to remember to do so at call sites.

## Decision
We will use [Django's CheckConstraints](https://docs.djangoproject.com/en/4.1/ref/models/constraints/#s-checkconstraint) to codify paired field relationships into the database.

## Consequences
We will have to put some more thought into our model creation and review to remember to add these constraints.
The same will apply to testing the constraints when we add them because coverage cannot tell us whether they have been tested.

We will also document how we use these constraints by adding some instructions into the developers.md.
