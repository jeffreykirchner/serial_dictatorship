# Generated by Django 5.2.1 on 2025-05-27 18:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0076_remove_parametersetplayer_id_label'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parametersetgroupperiod',
            name='parameter_set_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parameter_set_group_periods', to='main.parametersetgroup'),
        ),
    ]
