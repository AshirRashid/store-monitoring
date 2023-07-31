from django.http import JsonResponse
from django.db.models import Max
from .models import TimeZone, BusinessHours, Status, Report
from datetime import datetime, timedelta
from dateutil import tz


class CustomJsonResponse(JsonResponse):
    """Custom Reponse class to run a callback after the response is returned
    """

    def __init__(self, data, callback, report_id, **kwargs):
        super().__init__(data, **kwargs)
        self.callback = callback
        self.report_id = report_id

    def close(self):
        super().close()
        self.callback(self.report_id)


def trigger_report(_request) -> JsonResponse:
    """Returns a response with the report_id when report generation is triggered
    """
    report = Report()
    report.save()
    report_id = report.id
    return CustomJsonResponse({"report_id": report_id}, generate_report, report_id)


def get_report(request) -> JsonResponse:
    """Used to poll the database to check the status of the report with the report_id (passed through GET query parameters).
    A csv file is returned as text if the report generated has been completed
    """
    report_id = request.GET.get("report_id")
    relevant_reports = Report.objects.filter(id=report_id)
    if len(relevant_reports) == 0:
        return JsonResponse({"status": "report_id not found. No report has been generated with the given id"})
    else:
        report = list(relevant_reports)[0]
        if report.status == Report.RUNNING:
            return JsonResponse({"status": "Running"})
        elif report.status == Report.COMPLETE:
            return JsonResponse({"status": "Complete", "Data": report.data})


def generate_report(report_id):
    """Handles the report generation. Runs after the response to trigger_report is returned
    """
    print("GENERATING REPORT")
    report_str = ""
    current_time: datetime = list(
        Status.objects.aggregate(Max("timestamp")).values())[0]

    for timezone_record in TimeZone.objects.all():
        business_hours_records = BusinessHours.objects.filter(
            store_id=timezone_record)
        status_records = Status.objects.filter(store_id=timezone_record)

        # calculate up and down time last hour
        uptime_last_hour_min, downtime_last_hour_min = calc_up_down_time_last_hour(
            status_records, current_time)

        # calculate up and down time last day
        uptime_last_day_hrs, downtime_last_day_hrs = calc_up_down_time_last_day(
            status_records, business_hours_records, current_time)

        # calculate up and down time last week
        uptime_last_week_hrs, downtime_last_week_hrs = calc_up_down_time_last_week(
            status_records, business_hours_records, current_time)

        report_str += f"{timezone_record.store_id},{uptime_last_hour_min},{uptime_last_day_hrs},{uptime_last_week_hrs},{downtime_last_hour_min},{downtime_last_day_hrs},{downtime_last_week_hrs}\n"

    report = Report.objects.get(id=report_id)
    report.data, report.status = report_str, Report.COMPLETE
    report.save()


def calc_up_down_time_last_hour(status_records, current_time):
    two_hours_timedelta = timedelta(hours=1, minutes=59)
    relevant_records = status_records.filter(
        timestamp__gte=current_time - two_hours_timedelta)
    if len(relevant_records) == 0:
        uptime_last_hour = timedelta()
    else:
        relevant_timestamp = list(relevant_records.aggregate(
            Max("timestamp")).values())[0]
        uptime_last_hour = relevant_timestamp - \
            (current_time - timedelta(hours=1))

    # calculate downtime last hour
    downtime_last_hour = timedelta(hours=1) - uptime_last_hour

    return uptime_last_hour.total_seconds()/60, downtime_last_hour.total_seconds()/60


def calc_up_down_time_last_day(status_records, business_hours_records, current_time):
    """Uptime calculation:
            For every active status record:
            If 1) it is within business hours and 2) does not overlap with another active status record already taken into account,
            add one hour to the uptime
        Downtime calculation:
            Calculate total overlap between the business hours and the time span in question (one day from the current time)
            Subtract the uptime from the overlap
    """
    last_day_timestamp: datetime = current_time - timedelta(days=1)
    relevant_records = status_records.filter(
        timestamp__gte=last_day_timestamp).filter(status="active").order_by("timestamp")
    uptime_last_day = timedelta()
    hours_covered = []  # stores elements of the form (date, hours)
    for record in relevant_records:
        record_week_day = record.timestamp.weekday()
        relevant_business_hours = list(business_hours_records.filter(
            week_day=record_week_day))[0]
        if (
            record.timestamp > datetime.combine(
                record.timestamp.date(), relevant_business_hours.start_time_utc, tz.UTC)
            and record.timestamp < datetime.combine(
                record.timestamp.date(), relevant_business_hours.end_time_utc, tz.UTC)
            and (record.timestamp.date(), record.timestamp.hour) not in hours_covered
        ):
            hours_covered.append(
                (record.timestamp.date(), record.timestamp.hour))
            uptime_last_day += timedelta(hours=1)

    business_hours_last_week_day = last_day_timestamp.weekday()
    business_hours_current_week_day = last_day_timestamp.weekday()
    current_day_business_hours = business_hours_records.filter(
        week_day=business_hours_current_week_day)[0]
    last_day_business_hours = business_hours_records.filter(
        week_day=business_hours_last_week_day)[0]

    # calculate total_business_hours_span
    # placeholder_date to be used to convert datetime.time to datetime.datetime since datetime.time objects cannot be subtracted
    placeholder_date = datetime.now()
    total_business_hours_span = timedelta()
    if last_day_business_hours.start_time_utc > last_day_timestamp.time():
        total_business_hours_span += datetime.combine(placeholder_date, last_day_business_hours.end_time_utc) - datetime.combine(
            placeholder_date, last_day_business_hours.start_time_utc)
    elif last_day_business_hours.end_time_utc > last_day_timestamp.time():
        total_business_hours_span += datetime.combine(placeholder_date, last_day_business_hours.end_time_utc) - datetime.combine(
            placeholder_date, last_day_timestamp.time())

    if current_time.time() > current_day_business_hours.start_time_utc:
        if current_time.time() > current_day_business_hours.end_time_utc:
            total_business_hours_span += datetime.combine(placeholder_date, current_day_business_hours.end_time_utc) - datetime.combine(
                placeholder_date, current_day_business_hours.start_time_utc)
        else:
            total_business_hours_span += datetime.combine(placeholder_date, current_time.time()) - datetime.combine(
                placeholder_date, current_day_business_hours.start_time_utc)

    downtime_last_day: timedelta = total_business_hours_span - uptime_last_day
    if downtime_last_day.total_seconds() < 0:  # round off an error of up to one hour
        downtime_last_day = timedelta()

    return uptime_last_day.total_seconds()/3600, downtime_last_day.total_seconds()/3600


def calc_up_down_time_last_week(status_records, business_hours_records, current_time):
    idx_start = -current_time.weekday()
    idx_end = idx_start + 7
    up_down_time_per_day = [
        calc_up_down_time_last_day(
            status_records,
            business_hours_records,
            current_time + (timedelta() if idx == 0 else idx*timedelta(days=1))
        ) for idx in range(idx_start, idx_end)
    ]
    return sum([up_down_time_pair[0] for up_down_time_pair in up_down_time_per_day]), sum([up_down_time_pair[1] for up_down_time_pair in up_down_time_per_day])
