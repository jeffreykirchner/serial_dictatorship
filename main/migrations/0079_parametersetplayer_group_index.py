# Generated by Django 5.2.1 on 2025-05-28 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0078_alter_parametersetgroupperiod_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='parametersetplayer',
            name='group_index',
            field=models.IntegerField(default=0, verbose_name='Group index'),
        ),
    ]
