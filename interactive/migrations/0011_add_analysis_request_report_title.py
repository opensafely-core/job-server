# Generated by Django 4.1.7 on 2023-04-14 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("interactive", "0010_remove_analysis_request_complete_email_sent_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="analysisrequest",
            name="report_title",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
    ]
