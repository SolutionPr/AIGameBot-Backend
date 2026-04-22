from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Game", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="gameconfig",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                help_text="User who generated this config, if the request was authenticated.",
                null=True,
                on_delete=models.SET_NULL,
                related_name="game_configs",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
