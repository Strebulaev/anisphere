# Generated manually by assistant to add a GenericRelation field
from django.db import migrations
from django.contrib.contenttypes.fields import GenericRelation


def forwards(apps, schema_editor):
    # nothing to do here, the relation is managed by django at runtime
    pass


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0013_postmedia_media_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='favorites',
            field=GenericRelation(
                to='social.Favorite',
                related_query_name='posts',
            ),
        ),
    ]
