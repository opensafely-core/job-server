from .models import Report


def create_report(*, rfile, title, description="", user):
    return Report.objects.create(
        project=rfile.workspace.project,
        release_file=rfile,
        title=title,
        description="",
        created_by=user,
        updated_by=user,
    )
