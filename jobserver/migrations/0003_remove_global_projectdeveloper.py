from django.db import migrations

from jobserver.authorization.roles import DeploymentAdministrator, ProjectDeveloper


def replace_user_projectdeveloper_with_deploymentadministrator(apps, schema_editor):
    User = apps.get_model("jobserver", "User")
    for user in User.objects.filter(roles__contains=ProjectDeveloper):
        user.roles.remove(ProjectDeveloper)
        user.roles.append(DeploymentAdministrator)
        user.save()


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0002_remove_user_github_access_tokens"),
    ]

    operations = [
        migrations.RunPython(
            replace_user_projectdeveloper_with_deploymentadministrator
        ),
    ]
