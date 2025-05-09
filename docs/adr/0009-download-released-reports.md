# 9. Allow download of released reports

Date: 2023-02-22

## Status

Deprecated (see [ADR 29](0029-sunset-osi-interactive.md), sunsetting Interactive.

## Context

An Interactive report is a html document generated by an automated pipeline, as the result of an analysis request. When an Interactive report is generated, the report is produced from an output-checked result made available to Job Server as a "released output". The visibility of the released output and of the report is restricted to Job Server users who have access to the project or to Bennett Institute members who have been assigned the staff role.

It is expected that an Interactive report will need to be shared with the wider research team team or collaborators to be able to confirm its appropriateness/accuracy. We need to allow users to do that in a way that's in line with our policy for the ["sharing of results"](https://www.opensafely.org/policies-for-researchers/#details-all-datasets). Additionally, any reports that are deemed to be a "final" output will need to be sent to NHSE for approval to be made public.

We need a way to allow both types of sharing, while discouraging wider sharing. We also need a method that is quick and easy to use, otherwise we risk users trying to create insecure workarounds (such as sharing their account details).

### Options

1. We could use time-limited, unique links to share the reports.
We would generate a unique link for a given NHS.net email address and email it directly to them.
The link will stop working after a predefined time limit (e.g 2 hours or 2 days).
2. We could allow reports to be downloaded, using the browser's "print to PDF" option, with a prominent "draft, confidential" watermark on it. This would provide a PDF report with only basic formatting, but with all the explanatory text of the web-based version.


## Decision

We will provide a "download PDF" option, which uses the browser's print-to-PDF functionality, with a prominent "draft, confidential" watermark on it. This solution follows our existing process for sharing released outputs, matches up with our [policy](https://www.opensafely.org/policies-for-researchers/#details-all-datasets) and is in line with how NHSE currently work.

The report must also include details of rules/conditions of sharing and link to our policy (to place somewhere appropriate in the user flow for downloading reports) to remind users of their obligations regarding the distribution of the report.


## Consequences

### Download PDF
This would allow users to share the report internally as much as they’d like, but with the watermark it would be clear to them and others that it’s for internal use only.

This option provides less traceability. We wouldn't know who they were intending to share the report with and wouldn't be able to control it once it's downloaded, whereas we could disable a shareable link.

However, if we were to restrict downloading people could find a way to download it anyway. At least this provides some control by providing a warning and inserting a watermark.

### Shareable links
Anyone with the link will have access to view that report.

It's possible that an incorrect email address will be entered and the link sent to the wrong person. However, we could mitigate that by only allowing a specified set of domains, limited to nhs.net in the first instance. Any other email addresses would result in an error being returned to the user.

While this solution would be suitable for both collaborators and NHSE, we wouldn't need to use it for NHSE if not deemed appropriate. Alternatively, we could email a PDF copy of the report, generated by Bennett staff, as we anticipate there will be a low number of these requests in the short term.

### Alternatives
An alternative option could be to create restricted user accounts on Job Server for them to be able to view the reports. However, this creates a significant overhead, both to sharing the report quickly, and to the Bennett Institute for managing these user accounts. There is also a risk that a generic user account would be created for viewing reports, as has happened on reports.opensafely.org.
