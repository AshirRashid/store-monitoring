from django.db import models
from datetime import time


class TimeZone(models.Model):
    store_id = models.CharField(max_length=20, primary_key=True)
    timezone = models.CharField(max_length=30, default="America/Chicago")


class BusinessHours(models.Model):
    DEFAULT_START_TIME = time(hour=0, minute=0, second=0)
    DEFAULT_END_TIME = time(hour=23, minute=59, second=59)
    MON, TUE, WED, THU, FRI, SAT, SUN = range(7)

    store_id = models.ForeignKey(TimeZone, on_delete=models.CASCADE)
    week_day = models.CharField(max_length=1)
    start_time_utc = models.TimeField(
        auto_now=False, auto_now_add=False, default=DEFAULT_START_TIME)
    end_time_utc = models.TimeField(
        auto_now=False, auto_now_add=False, default=DEFAULT_END_TIME)


class Status(models.Model):
    store_id = models.ForeignKey(TimeZone, on_delete=models.CASCADE)
    status = models.CharField(max_length=8)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=False)  # UTC


class Report(models.Model):
    # id autoset
    RUNNING = "Running"
    COMPLETE = "Complete"

    STATUS_CHOICES = (
        (RUNNING, "Generating Report"),
        (COMPLETE, "Report Available")
    )

    status = models.CharField(
        max_length=8,
        choices=STATUS_CHOICES,
        default=RUNNING,
    )
    data = models.TextField(default="")
