# Generated by Django 5.1.3 on 2024-11-30 21:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_userreaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userreaction',
            name='news',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='news.news'),
        ),
    ]
