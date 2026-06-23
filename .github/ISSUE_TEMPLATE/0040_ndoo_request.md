---
name: National Data Opt-Out request
about: Request from the service team to allow a project to query patients who have opted out under NDOO
title: Add project [PROJECT NUMBER] to NDOO permissions list
labels: "tech-support-ndoo"
assignees: ""
---

Add a project to the National Data Opt-Out permissions list. This will grant the project permission to query patients with any NDOO status.

You should not create this issue if a project has requested to apply the National Data Opt-Out. ehrQL will exclude patients who have opted out under NDOO by default, so no extra configuration is needed.
- Project number: [PROJECT NUMBER]
- Project name: [PROJECT NAME]


When a member of the OpenSAFELY service team creates this issue, they should:
1. Fill in the project name and number above
1. Post a Slack message with a link to the issue, and mention tech-support
1. Wait for tech-support to confirm that the project permissions have been updated before allowing the project to start running jobs on the backend


Whoever is on tech-support should [follow the instructions in the playbook](https://bennett.wiki/tech-group/tech-support/playbook/#requests-for-national-data-opt-out-ndoo-permissions) to configure the project.
