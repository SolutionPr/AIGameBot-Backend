# Generated to support the three-step password reset flow.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_drop_username_unique_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="passwordresetotp",
            name="is_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="passwordresetotp",
            name="verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
