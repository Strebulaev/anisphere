# Generated migration for Comment reply_to and is_edited fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0012_achievement_attachment_chatinvite_emaillog_favorite_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='reply_to',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='answer_to',
                to='social.comment',
                verbose_name='Ответ на комментарий'
            ),
        ),
        migrations.AddField(
            model_name='comment',
            name='is_edited',
            field=models.BooleanField(default=False, verbose_name='Редактирован'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(
                fields=['parent', 'created_at'],
                name='social_com_mother_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(
                fields=['reply_to', 'created_at'],
                name='social_com_reply_idx'
            ),
        ),
    ]
