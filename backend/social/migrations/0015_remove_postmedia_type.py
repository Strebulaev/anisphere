"""
Migration to remove the legacy 'type' column from social_postmedia table.

Background:
- Migration 0012 created PostMedia with a 'type' field (no default value).
- Migration 0013 added a new 'media_type' field (with default='image').
- The model was updated to use 'media_type', but the old 'type' column was
  never removed from the database, causing MySQL IntegrityError 1364:
  "Field 'type' doesn't have a default value" on every INSERT.

This migration removes the stale 'type' column.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0014_add_post_favorites'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postmedia',
            name='type',
        ),
    ]
