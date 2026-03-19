from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0014_missing_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupchat',
            name='members_count',
            field=models.IntegerField(default=0),
        ),
    ]
