# Generated by Django 5.2.1 on 2025-05-28 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0080_parametersetgroupperiod_priority_scores'),
    ]

    operations = [
        migrations.AddField(
            model_name='parametersetgroupperiod',
            name='player_order',
            field=models.CharField(blank=True, max_length=1000, null=True, verbose_name='1,2,3,4'),
        ),
    ]
