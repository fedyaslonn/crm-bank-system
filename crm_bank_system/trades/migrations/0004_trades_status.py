# Generated by Django 5.1.3 on 2024-12-03 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0003_trades_card_alter_trades_amount_from_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='trades',
            name='status',
            field=models.CharField(choices=[('ACTIVE', 'Active'), ('FROZEN', 'Frozen'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')], default='ACTIVE', verbose_name='Статус трейда'),
        ),
    ]
