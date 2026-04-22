from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_passwordresetotp_verification_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="profile",
            name="phone_number",
        ),
        migrations.RemoveField(
            model_name="profile",
            name="date_of_birth",
        ),
        migrations.AddField(
            model_name="profile",
            name="games_created",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="profile",
            name="games_played",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="profile",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
