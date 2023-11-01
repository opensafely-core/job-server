# ***************************************************************************
# ANY CHANGES TO THE LOGIC BELOW MUST BE EXPLICITLY APPROVED BY THE IG TEAM *
# ***************************************************************************


def project_is_permitted_to_use_sqlrunner(project):
    return project.pk == 28  # This is the opensafely-internal project
