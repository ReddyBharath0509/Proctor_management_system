# Generated by Django 5.1.7 on 2025-04-02 07:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_panel", "0001_initial"),
        ("teacher", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="timeslot",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="timeslot",
            name="day",
            field=models.IntegerField(
                choices=[
                    (0, "Monday"),
                    (1, "Tuesday"),
                    (2, "Wednesday"),
                    (3, "Thursday"),
                    (4, "Friday"),
                    (5, "Saturday"),
                    (6, "Sunday"),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="timeslot",
            name="teacher",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="time_slots",
                to="teacher.teacher",
            ),
        ),
        migrations.AlterField(
            model_name="timeslot",
            name="time",
            field=models.IntegerField(
                choices=[
                    (1, "9:00 AM - 10:00 AM"),
                    (2, "10:00 AM - 11:00 AM"),
                    (3, "11:00 AM - 12:00 PM"),
                    (4, "12:00 PM - 1:00 PM"),
                    (5, "2:00 PM - 3:00 PM"),
                    (6, "3:00 PM - 4:00 PM"),
                    (7, "4:00 PM - 5:00 PM"),
                ]
            ),
        ),
    ]
