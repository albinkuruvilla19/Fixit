# Generated by Django 5.1.5 on 2025-01-24 06:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0009_remove_customer_address_remove_customer_latitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='subsubcategory',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='Home.subsubcategory'),
        ),
    ]
