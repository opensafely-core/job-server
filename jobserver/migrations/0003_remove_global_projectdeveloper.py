from django.db import migrations

from jobserver.authorization.roles import DeploymentAdministrator, ProjectDeveloper


def change_user_role(apps, from_role, to_role):
    User = apps.get_model("jobserver", "User")
    for user in User.objects.filter(roles__contains=from_role):
        user.roles.remove(from_role)
        user.roles.append(to_role)
        user.save()


def replace_user_projectdeveloper_with_deploymentadministrator(apps, schema_editor):
    change_user_role(apps, ProjectDeveloper, DeploymentAdministrator)


def replace_user_deploymentadministrator_with_projectdeveloper(apps, schema_editor):
    change_user_role(apps, DeploymentAdministrator, ProjectDeveloper)


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0002_remove_user_github_access_tokens"),
    ]

    operations = [
        migrations.RunPython(
            replace_user_projectdeveloper_with_deploymentadministrator,
            reverse_code=replace_user_deploymentadministrator_with_projectdeveloper,
        ),
    ]
