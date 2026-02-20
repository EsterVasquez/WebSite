from datetime import datetime, timedelta

from app.models import Booking
from app.services.chat_service import mark_chat_needs_attention, mark_chat_resolved


def list_dashboard_bookings() -> list[dict]:
    bookings = (
        Booking.objects.select_related("user", "user__chat_conversation", "service", "package")
        .all()
        .order_by("date", "time")
    )
    rows: list[dict] = []
    for booking in bookings:
        chat = getattr(booking.user, "chat_conversation", None)
        has_pending_chat = chat is not None and chat.status == "pending"
        status_code = booking.status
        status_label = booking.get_status_display()
        if has_pending_chat and booking.status != Booking.Status.CANCELLED:
            status_code = Booking.Status.DOUBTS
            status_label = "Dudas"
        rows.append(
            {
                "id": booking.id,
                "user_name": booking.customer_name or booking.user.name or "Cliente",
                "phone_number": booking.customer_phone or booking.user.phone_number,
                "service": booking.service.name,
                "package": booking.package.name if booking.package else "Sin paquete",
                "duration_minutes": booking.duration_minutes,
                "date": booking.date.isoformat(),
                "time": booking.time.strftime("%H:%M"),
                "status_code": status_code,
                "status": status_label,
                "source": booking.get_source_display(),
                "total_price": float(booking.total_price),
                "deposit_amount": float(booking.deposit_amount),
                "customer_notes": booking.customer_notes or "",
                "chat_pending": has_pending_chat,
                "chat_user_id": booking.user_id if has_pending_chat else None,
            }
        )
    return rows


def update_booking_status(*, booking_id: int, status_code: str) -> Booking:
    booking = Booking.objects.get(id=booking_id)
    valid_statuses = {choice[0] for choice in Booking.Status.choices}
    if status_code not in valid_statuses:
        raise ValueError("Estado de reservación inválido.")
    booking.status = status_code
    booking.save(update_fields=["status", "updated_at"])
    if status_code == Booking.Status.DOUBTS:
        mark_chat_needs_attention(booking.user)
    elif status_code in {Booking.Status.CONFIRMED, Booking.Status.CANCELLED}:
        conversation = getattr(booking.user, "chat_conversation", None)
        if conversation and conversation.status == "pending":
            mark_chat_resolved(booking.user)
    return booking


def list_booking_events() -> list[dict]:
    bookings = Booking.objects.select_related("service", "package").all()
    events: list[dict] = []
    for booking in bookings:
        start_dt = datetime.combine(booking.date, booking.time)
        end_dt = start_dt + timedelta(minutes=max(booking.duration_minutes, 1))
        color = "#0f766e"
        if booking.status == Booking.Status.PENDING:
            color = "#b45309"
        elif booking.status == Booking.Status.CONFIRMED:
            color = "#166534"
        elif booking.status == Booking.Status.CANCELLED:
            color = "#b91c1c"
        events.append(
            {
                "id": booking.id,
                "title": f"{booking.service.name} - {booking.customer_name or 'Cliente'}",
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "allDay": False,
                "backgroundColor": color,
                "borderColor": color,
                "extendedProps": {
                    "phone_number": booking.customer_phone,
                    "status": booking.get_status_display(),
                    "package": booking.package.name if booking.package else "Sin paquete",
                    "source": booking.get_source_display(),
                    "service": booking.service.name,
                    "notes": booking.customer_notes or "",
                },
            }
        )
    return events
