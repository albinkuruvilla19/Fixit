# Generated by Django 5.1.5 on 2025-01-19 12:11

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0004_bookingquestion_subcategory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='time',
            field=models.TimeField(choices=[(datetime.time(9, 0), '9:00 AM'), (datetime.time(9, 30), '9:30 AM'), (datetime.time(10, 0), '10:00 AM'), (datetime.time(10, 30), '10:30 AM'), (datetime.time(11, 0), '11:00 AM'), (datetime.time(11, 30), '11:30 AM'), (datetime.time(12, 0), '12:00 PM'), (datetime.time(12, 30), '12:30 PM'), (datetime.time(13, 0), '1:00 PM'), (datetime.time(13, 30), '1:30 PM'), (datetime.time(14, 0), '2:00 PM'), (datetime.time(14, 30), '2:30 PM'), (datetime.time(15, 0), '3:00 PM'), (datetime.time(15, 30), '3:30 PM'), (datetime.time(16, 0), '4:00 PM'), (datetime.time(16, 30), '4:30 PM'), (datetime.time(17, 0), '5:00 PM'), (datetime.time(17, 30), '5:30 PM'), (datetime.time(18, 0), '6:00 PM'), (datetime.time(18, 30), '6:30 PM'), (datetime.time(19, 0), '7:00 PM'), (datetime.time(19, 30), '7:30 PM'), (datetime.time(20, 0), '8:00 PM'), (datetime.time(20, 30), '8:30 PM'), (datetime.time(21, 0), '9:00 PM'), (datetime.time(21, 30), '9:30 PM'), (datetime.time(22, 0), '10:00 PM')]),
        ),
    ]
