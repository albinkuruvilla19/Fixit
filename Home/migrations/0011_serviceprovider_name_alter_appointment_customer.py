# Generated by Django 5.1.5 on 2025-01-27 14:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0010_appointment_subsubcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceprovider',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer', to='Home.customer'),
        ),
    ]
