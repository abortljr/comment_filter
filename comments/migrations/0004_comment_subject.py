# Generated by Django 2.1.1 on 2022-07-18 18:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0003_comment_screened'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='subject',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='subject'),
        ),
    ]
