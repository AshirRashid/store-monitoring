from gdown import download
from django.core.management.base import BaseCommand
from django.db import transaction
from ...models import TimeZone, BusinessHours, Status
from time import perf_counter
from datetime import datetime, time
from dateutil import tz


FILE_NAME_2_IDS = {
    "status.csv": "1UIx1hVJ7qt_6oQoGZgb8B3P2vd1FD025",
    "business_hours.csv": "1va1X3ydSh-0Rt1hsy2QSnHRA4w57PcXg",
    "timezone.csv": "101P9quxHoMZMZCVWQ5o-shonk2lgK1-o",
}


def _download_data_files() -> None:
    for file_name, id in FILE_NAME_2_IDS.items():
        download(id=id, output=file_name)


def load_data_in_db() -> None:
    start = perf_counter()
    _download_data_files()
    next_start = perf_counter()
    print("FILE DOWNLOADED", next_start-start)
    start = next_start
    file_names = list(FILE_NAME_2_IDS.keys())
    print("POPULATING TIMEZONE DB")
    with transaction.atomic():
        with open(file_names[2]) as timezone_file:
            timezone_file.readline()
            for timezone_line in timezone_file:
                store_id, timezone_str = timezone_line.split(',')
                timezone_record = TimeZone(
                    store_id=store_id, timezone=timezone_str)
                timezone_record.save()

        # check if the store id is in TimeZone. If not, initialize with default value i.e. "America/Chicago"
        next_start = perf_counter()
        print("POPULATED TIMEZONE DB", next_start-start)
        start = next_start
        print("POPULATING STATUS DB")
        with open(file_names[0]) as status_file:
            status_file.readline()
            for status_line in status_file:
                store_id, status_str, timestamp_utc = status_line.split(',')
                try:
                    timezone_record = TimeZone.objects.get(store_id=store_id)
                except TimeZone.DoesNotExist:
                    timezone_record = TimeZone(store_id=store_id)
                    timezone_record.save()

                # remove the " UTC" from the end
                processed_timestamp_utc = timestamp_utc[:-5]
                if "." in processed_timestamp_utc:  # there is microsecond information
                    timestamp_format = "%Y-%m-%d %H:%M:%S.%f"
                else:
                    timestamp_format = "%Y-%m-%d %H:%M:%S"

                datetime_timestamp_utc = datetime.strptime(
                    processed_timestamp_utc, timestamp_format)

                status_record = Status(
                    store_id=timezone_record,
                    status=status_str,
                    timestamp=datetime_timestamp_utc
                )
                status_record.save(0)
        next_start = perf_counter()
        print("POPULATED STATUS DB", next_start-start)
        start = next_start

        # check if the store id is in TimeZone. If not, initialize with default value i.e. "America/Chicago"
        print("POPULATING BUSINESS HOURS DB")
        with open(file_names[1]) as business_hours_file:
            business_hours_file.readline()
            for business_hours_line in business_hours_file:
                store_id, week_day_char, start_time_str, end_time_str = business_hours_line.split(
                    ',')
                try:
                    timezone_record = TimeZone.objects.get(store_id=store_id)
                except TimeZone.DoesNotExist:
                    timezone_record = TimeZone(store_id=store_id)
                    timezone_record.save()

                start_time_utc = business_hours_local_to_utc(
                    start_time_str, timezone_record.timezone)
                end_time_utc = business_hours_local_to_utc(
                    end_time_str, timezone_record.timezone)
                business_hours_record = BusinessHours(
                    store_id=timezone_record,
                    week_day=week_day_char,
                    start_time_utc=start_time_utc,
                    end_time_utc=end_time_utc
                )
                business_hours_record.save(0)
        next_start = perf_counter()
        print("POPULATED BUSINESS HOURS DB", next_start-start)
        start = next_start

        print("POPULATING DEFAULT VALUES FOR BUSINESS HOURS DB")
        print(len(TimeZone.objects.all()))
        for timezone_record in TimeZone.objects.all():
            for week_day in [str(week_day_int) for week_day_int in range(7)]:
                matching_business_hours = BusinessHours.objects.filter(
                    store_id=timezone_record, week_day=week_day
                )
                if len(matching_business_hours) == 0:
                    business_hours_record = BusinessHours(
                        store_id=timezone_record, week_day=week_day
                    )
                    business_hours_record.save()
        next_start = perf_counter()
        print("POPULATED DEFAULT VALUES FOR BUSINESS HOURS DB", next_start-start)
        start = next_start


def business_hours_local_to_utc(business_hours_str, timezone_str):
    try:
        datetime_time_local = datetime.strptime(
            business_hours_str.strip(), "%H:%M:%S")
    except:
        breakpoint()
    local_timezone = tz.gettz(timezone_str)
    datetime_time_local.replace(tzinfo=local_timezone)
    return datetime_time_local.astimezone(tz.UTC).time()


class Command(BaseCommand):
    help = "Retrieve csv files from google drive using the gdown package and load the data they contain into the database"

    def handle(self, *args, **kwargs):
        load_data_in_db()
