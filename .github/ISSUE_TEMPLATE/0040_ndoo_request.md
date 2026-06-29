---
name: National Data Opt-Out request
about: Request from the service team to allow projects to query patients who have opted out under NDOO
title: Add projects to NDOO permissions list
labels: "tech-support-ndoo"
assignees: ""
---

Add projects to the National Data Opt-Out permissions list. This will grant the projects permission to query patients with any NDOO status.

You should not include projects that have requested to apply the National Data Opt-Out. ehrQL will exclude patients who have opted out under NDOO by default, so no extra configuration is needed.

- [FIRST PROJECT NUMBER]: [FIRST PROJECT NAME]
- [SECOND PROJECT NUMBER]: [SECOND PROJECT NAME]
- ... add more as needed

When a member of the OpenSAFELY service team creates this issue, they should:
1. Fill in the project names and numbers above
1. Post a Slack message with a link to the issue, and mention tech-support
1. Wait for tech-support to confirm that the project permissions have been updated before allowing the projects to start running jobs on the backend

Whoever is on tech-support should [follow the instructions in the playbook](https://bennett.wiki/tech-group/tech-support/playbook/#requests-for-national-data-opt-out-ndoo-permissions) to configure the projects.
