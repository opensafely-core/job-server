# *******************
#   IMPORTANT NOTE  *
# *******************
#
# Only the IG team are authorised to make modifications to the list of projects below.
# Any PRs which update this list should be reviewed and approved by a member of the IG
# team so as to create the appropriate audit trail.
#
# Note also that this file is linked to in the documentation. If you move or restructure
# this file you should ensure the documentation is updated appropriately.
# https://github.com/opensafely/documentation/blob/af88baf1/docs/type-one-opt-outs.md


def project_is_permitted_to_use_sqlrunner(project):
    return project.pk == 28  # This is the opensafely-internal project
