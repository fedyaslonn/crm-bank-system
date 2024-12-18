# Generated by Django 5.1.3 on 2024-11-29 22:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(verbose_name='Описание проблемы')),
                ('screenshot', models.URLField(blank=True, null=True, verbose_name='URL скриншота')),
                ('status', models.CharField(blank=True, choices=[('PENDING', 'Pending'), ('RESOLVED', 'Resolved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10, null=True, verbose_name='Статус жалобы')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Дата обновления')),
                ('document_url', models.URLField(blank=True, null=True, verbose_name='URL документа Word')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Жалоба',
                'verbose_name_plural': 'Жалобы',
                'db_table': 'Reports',
                'ordering': ['-created_at'],
            },
        ),
    ]
