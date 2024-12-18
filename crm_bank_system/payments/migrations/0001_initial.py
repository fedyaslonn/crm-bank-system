# Generated by Django 5.1.3 on 2024-11-29 22:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SalaryDeposit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Сумма пополнения')),
                ('deposited_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата пополнения')),
                ('card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_deposits', to='users.userclientcard')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_deposits', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Пополнение зарплаты',
                'verbose_name_plural': 'Пополнения зарплаты',
                'db_table': 'SalaryDeposit',
                'ordering': ['-deposited_at'],
            },
        ),
    ]
