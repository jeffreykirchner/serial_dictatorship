# Generated by Django 5.2.1 on 2025-05-28 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0077_alter_parametersetgroupperiod_parameter_set_group'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='parametersetgroupperiod',
            options={'ordering': ['parameter_set_group__name', 'period_number'], 'verbose_name': 'Parameter Set Group Period', 'verbose_name_plural': 'Parameter Set Group Periods'},
        ),
        migrations.AlterField(
            model_name='parametersetgroupperiod',
            name='values',
            field=models.CharField(blank=True, max_length=1000, null=True, verbose_name='0.00,0.25,0.75,1.00'),
        ),
    ]
