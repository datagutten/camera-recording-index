# Generated by Django 5.2.1 on 2025-06-07 20:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recordings', '0004_recording_mtime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recording',
            name='camera',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recordings', to='recordings.camera'),
        ),
    ]
