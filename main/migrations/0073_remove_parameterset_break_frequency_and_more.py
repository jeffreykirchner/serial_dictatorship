# Generated by Django 5.2.1 on 2025-05-23 17:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0072_remove_parameterset_avatar_animation_speed_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='parameterset',
            name='break_frequency',
        ),
        migrations.RemoveField(
            model_name='parameterset',
            name='break_length',
        ),
    ]
