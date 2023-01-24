# 3. Creating Interactive queries

Date: 2022-04-14

## Status

Accepted

## Context

*Note: this was originally written for the standalone Interactive application and has been moved across as part of the integration into Job Server. The original ADR can be found [here](https://github.com/opensafely-core/interactive.opensafely.org/blob/main/docs/adr/0003-creating-interactive-queries.md).*

Each time someone requests an analysis using OpenSafely Interactive, a study will need to be updated and saved to a GitHub repository. This is required both by the Job Server in order to run the query and for our current audit approach which repies upon having tamper-resistant git commit log.

We have several approaches that we could take for this:
1. Add a new action into the project.yaml for each request.

    In reality, this will require several actions as we'll have multiple study definitions and analysis steps. It will make the project.yaml hard to read for humans and will also require regular maintenance to prevent it from becoming too unweldy.


2. Create a new GitHub repo for each request.

    This follows our existing conventions for manual queries. However, it requires additional permissions in GitHub to create repos. This could be mitigated by using a separate GitHub organisation . It also requires regular maintenance to prevent the proliferation of repos, Job Server workspaces and storage in Job Runner.

3. Overwrite the study definition and/or project.yaml for each analysis request.

    i.e Treat each request as a separate commit. This preserves our current audit approach. Links to specific code still work, Job Server behaves as expected and all code is visible in the tamper-resistant git commit log.



## Decision

*Option 3. Overwrite the study definition and/or project.yaml for each analysis request.*

Each request will produce a new commit in a shared GitHub repo within the OpenSafely GitHub organisation. This will overwrite any previous study settings, such as the codelist to be used. This will result in each request being represented by single commit and therefore a unique git SHA.

A JobRequest requires a specific git SHA, so when we submit the job for this query to Job Server, we will use the specific commit SHA, rather than HEAD. Job Server and Job Runner will happily run the project.yaml version from that specific commit. We'll have a single place in Job Server to manage the jobs, outputs and the audit trail.


## Consequences

This is nice because:
1. It preserves our current audit approach. Links to specific code still work, and all code is visible in the tamper-resistant git commit log. The commit log is **the** history of interactive queries.
2. The project.yaml will not grow in size over time, as each commit will contain only the changes needed to the run that specific query at that specific commit. Simpler to debug and run locally too.
3. We can add the requesting user in the commit metadata and in the Job Server database, further improving the audit trail
4. We can tag the commit with the id of the interactive query, which is nice for debugging, e.g `git checkout $INTERACTIVE_QUERY_ID` should get us the code for that query for debugging.
5. It still satisfies the security constraint we have that the SHA is on the branch.

Possible issues:
1. We'd lose the ability to easily re-run a failed job via the Job Server UI for debugging, unless it happens to be the most recent interactive query, as you cannot currently specify a SHA via the UI, it will use HEAD.

    Possible mitigation: add a re-submit job button to the JobRequest view to enable easy re-running of old interactive queries for debugging. This would be a useful addition in general.
