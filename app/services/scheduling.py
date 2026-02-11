from datetime import date, datetime, time, timedelta

from app.models import Booking, Feriado, ServiceTier, TimeBlock


WEEKDAY_MAP = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}


def _to_dt(target_date: date, target_time: time) -> datetime:
    return datetime.combine(target_date, target_time)


def _overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and start_b < end_a


def _service_available_on_date(tier: ServiceTier, target_date: date) -> bool:
    service = tier.service
    if target_date < service.available_from:
        return False
    if service.available_until and target_date > service.available_until:
        return False
    if Feriado.objects.filter(fecha=target_date).exists():
        return False
    weekday_name = WEEKDAY_MAP[target_date.weekday()]
    return service.days.filter(day=weekday_name).exists()


def _booked_intervals(target_date: date) -> list[tuple[datetime, datetime]]:
    bookings = (
        Booking.objects.select_related("service_tier")
        .filter(date=target_date)
        .exclude(status="Cancelado")
    )

    intervals: list[tuple[datetime, datetime]] = []
    for booking in bookings:
        start = _to_dt(target_date, booking.time)
        end = start + timedelta(minutes=booking.service_tier.duration_minutes)
        intervals.append((start, end))
    return intervals


def get_available_slots(tier: ServiceTier, target_date: date, slot_step_minutes: int = 30) -> list[time]:
    if not _service_available_on_date(tier, target_date):
        return []

    weekday_name = WEEKDAY_MAP[target_date.weekday()]
    blocks = TimeBlock.objects.filter(
        service=tier.service,
        day__day=weekday_name,
    ).order_by("start_time")

    if not blocks.exists():
        return []

    duration = timedelta(minutes=tier.duration_minutes)
    step = timedelta(minutes=slot_step_minutes)
    taken_intervals = _booked_intervals(target_date)
    available: list[time] = []

    for block in blocks:
        block_start = _to_dt(target_date, block.start_time)
        block_end = _to_dt(target_date, block.end_time)

        current = block_start
        while current + duration <= block_end:
            candidate_start = current
            candidate_end = current + duration
            has_collision = any(
                _overlaps(candidate_start, candidate_end, booked_start, booked_end)
                for booked_start, booked_end in taken_intervals
            )
            if not has_collision:
                available.append(candidate_start.time())
            current += step

    return available


def is_slot_available(tier: ServiceTier, target_date: date, target_time: time) -> bool:
    slots = get_available_slots(tier=tier, target_date=target_date)
    return target_time in slots
