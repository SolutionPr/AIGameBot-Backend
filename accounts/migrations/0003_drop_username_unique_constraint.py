# Generated to allow duplicate usernames while keeping email unique at the API level.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_passwordresetotp"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE auth_user DROP CONSTRAINT IF EXISTS auth_user_username_key;",
            reverse_sql="ALTER TABLE auth_user ADD CONSTRAINT auth_user_username_key UNIQUE (username);",
        ),
    ]
