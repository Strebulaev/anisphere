from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("anime", "0016_announcement_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="anime",
            name="is_available",
            field=models.BooleanField(
                default=True, verbose_name="Доступно для просмотра"
            ),
        ),
    ]
