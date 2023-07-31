# Generated by Django 4.2.3 on 2023-07-26 13:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TimeZone",
            fields=[
                (
                    "store_id",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                (
                    "timezone",
                    models.CharField(default="America/Chicago", max_length=30),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Status",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("status", models.CharField(max_length=8)),
                ("timestamp", models.CharField(max_length=31)),
                (
                    "store_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="api.timezone"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BusinessHours",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("week_day", models.CharField(max_length=1)),
                (
                    "start_time_local",
                    models.CharField(default="00:00:00", max_length=8),
                ),
                ("end_time_local", models.CharField(default="23:59:59", max_length=8)),
                (
                    "store_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="api.timezone"
                    ),
                ),
            ],
        ),
    ]