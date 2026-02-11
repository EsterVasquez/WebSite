from app.models import Booking


def list_dashboard_bookings() -> list[dict]:
    bookings = (
        Booking.objects.select_related("user", "service_tier", "service_tier__service")
        .all()
        .order_by("date", "time")
    )

    rows: list[dict] = []
    for booking in bookings:
        rows.append(
            {
                "id": booking.id,
                "user_name": booking.user.name or "Cliente",
                "phone_number": booking.user.phone_number,
                "service": booking.service_tier.service.name,
                "tier": booking.service_tier.name,
                "duration_minutes": booking.service_tier.duration_minutes,
                "date": booking.date.isoformat(),
                "time": booking.time.strftime("%H:%M"),
                "status": booking.status,
                "source": booking.source,
            }
        )
    return rows
