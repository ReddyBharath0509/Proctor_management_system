# Generated by Django 5.1.7 on 2025-04-02 05:00

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("student", "0002_initial"),
        ("teacher", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="attendance",
            options={"ordering": ["-date"]},
        ),
        migrations.AlterModelOptions(
            name="marks",
            options={"ordering": ["-date"]},
        ),
        migrations.AlterUniqueTogether(
            name="attendance",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="attendance",
            name="remarks",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="attendance",
            name="subject",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="marks",
            name="date",
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="marks",
            name="remarks",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="student",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="attendance",
            name="student",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attendance_records",
                to="student.student",
            ),
        ),
        migrations.AlterField(
            model_name="marks",
            name="student",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="marks",
                to="student.student",
            ),
        ),
        migrations.AlterField(
            model_name="student",
            name="assigned_proctor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="students",
                to="teacher.teacher",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="attendance",
            unique_together={("student", "subject", "date")},
        ),
        migrations.AlterUniqueTogether(
            name="marks",
            unique_together={("student", "subject", "semester")},
        ),
    ]
