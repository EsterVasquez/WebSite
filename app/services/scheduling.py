from datetime import date, datetime, time, timedelta

from app.models import Booking, Service, ServiceException, ServicePackage


def _to_dt(target_date: date, target_time: time) -> datetime:
    return datetime.combine(target_date, target_time)


def _overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and start_b < end_a


def _is_service_available_on_date(service: Service, target_date: date) -> bool:
    if not service.is_active:
        return False
    if service.available_from and target_date < service.available_from:
        return False
    if service.available_until and target_date > service.available_until:
        return False
    return True


def _base_ranges(service: Service, target_date: date) -> list[tuple[time, time]]:
    rows = service.weekly_ranges.filter(weekday=target_date.weekday()).order_by("order_index", "start_time")
    return [(row.start_time, row.end_time) for row in rows]


def _exception_ranges(service: Service, target_date: date) -> list[tuple[time, time]]:
    exceptions = service.exceptions.filter(date=target_date, is_active=True).order_by("id")
    if not exceptions.exists():
        return _base_ranges(service, target_date)

    if exceptions.filter(exception_type=ServiceException.ExceptionType.CLOSED).exists():
        return []

    ranges = _base_ranges(service, target_date)
    replacements = exceptions.filter(
        exception_type=ServiceException.ExceptionType.SPECIAL_RANGE,
        range_mode=ServiceException.RangeMode.REPLACE,
    )
    if replacements.exists():
        ranges = [
            (exception.start_time, exception.end_time)
            for exception in replacements
            if exception.start_time and exception.end_time
        ]

    additions = exceptions.filter(
        exception_type=ServiceException.ExceptionType.SPECIAL_RANGE,
        range_mode=ServiceException.RangeMode.ADD,
    )
    ranges.extend(
        (exception.start_time, exception.end_time)
        for exception in additions
        if exception.start_time and exception.end_time
    )
    return ranges


def _max_bookings_for_date(service: Service, target_date: date) -> int | None:
    exception = (
        service.exceptions.filter(
            date=target_date,
            is_active=True,
            exception_type=ServiceException.ExceptionType.MAX_BOOKINGS,
        )
        .order_by("-id")
        .first()
    )
    if not exception:
        return None
    return exception.max_bookings


def _booked_intervals(service: Service, target_date: date) -> list[tuple[datetime, datetime]]:
    bookings = (
        Booking.objects.filter(service=service, date=target_date)
        .exclude(status=Booking.Status.CANCELLED)
        .order_by("time")
    )
    intervals: list[tuple[datetime, datetime]] = []
    for booking in bookings:
        start = _to_dt(target_date, booking.time)
        end = start + timedelta(minutes=booking.duration_minutes)
        intervals.append((start, end))
    return intervals


def _bookings_count(service: Service, target_date: date) -> int:
    return (
        Booking.objects.filter(service=service, date=target_date)
        .exclude(status=Booking.Status.CANCELLED)
        .count()
    )


def get_available_slots(
    *,
    service: Service,
    target_date: date,
    duration_minutes: int,
    booking_interval_minutes: int | None = None,
    package: ServicePackage | None = None,
) -> list[time]:
    if not _is_service_available_on_date(service, target_date):
        return []

    ranges = _exception_ranges(service, target_date)
    if not ranges:
        return []

    day_limit = _max_bookings_for_date(service, target_date)
    if day_limit is not None and _bookings_count(service, target_date) >= day_limit:
        return []

    if package and package.max_bookings is not None:
        package_count = (
            Booking.objects.filter(service=service, package=package, date=target_date)
            .exclude(status=Booking.Status.CANCELLED)
            .count()
        )
        if package_count >= package.max_bookings:
            return []

    duration = timedelta(minutes=max(duration_minutes, 1))
    interval = timedelta(minutes=max(booking_interval_minutes or service.booking_interval_minutes, 5))
    taken_intervals = _booked_intervals(service, target_date)
    available: list[time] = []

    for start_time, end_time in ranges:
        block_start = _to_dt(target_date, start_time)
        block_end = _to_dt(target_date, end_time)
        current = block_start
        while current + duration <= block_end:
            candidate_start = current
            candidate_end = current + duration
            collision = any(
                _overlaps(candidate_start, candidate_end, booked_start, booked_end)
                for booked_start, booked_end in taken_intervals
            )
            if not collision:
                available.append(candidate_start.time())
            current += interval

    return available


def is_slot_available(
    *,
    service: Service,
    target_date: date,
    target_time: time,
    duration_minutes: int,
    booking_interval_minutes: int | None = None,
    package: ServicePackage | None = None,
) -> bool:
    slots = get_available_slots(
        service=service,
        target_date=target_date,
        duration_minutes=duration_minutes,
        booking_interval_minutes=booking_interval_minutes,
        package=package,
    )
    return target_time in slots


def get_day_availability_status(
    *,
    service: Service,
    target_date: date,
    duration_minutes: int,
    booking_interval_minutes: int | None = None,
    package: ServicePackage | None = None,
) -> dict:
    if not _is_service_available_on_date(service, target_date):
        return {"status": "out_of_range", "available_slots": 0}

    ranges = _exception_ranges(service, target_date)
    if not ranges:
        return {"status": "no_schedule", "available_slots": 0}

    slots = get_available_slots(
        service=service,
        target_date=target_date,
        duration_minutes=duration_minutes,
        booking_interval_minutes=booking_interval_minutes,
        package=package,
    )
    if slots:
        return {"status": "available", "available_slots": len(slots)}
    return {"status": "full", "available_slots": 0}
