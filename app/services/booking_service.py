from datetime import datetime
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction

from app.models import Booking, BookingIntent, Service, ServiceTier, User
from app.services.scheduling import get_available_slots, is_slot_available


def create_booking_intent(user: User, service: Service, payload_id: str) -> BookingIntent:
    default_tier = (
        service.tiers.filter(is_default=True).order_by("price").first()
        or service.tiers.order_by("price").first()
    )

    with transaction.atomic():
        BookingIntent.objects.filter(
            user=user,
            status=BookingIntent.Status.OPEN,
        ).update(status=BookingIntent.Status.CANCELLED)

        return BookingIntent.objects.create(
            user=user,
            service=service,
            selected_tier=default_tier,
            source_payload_id=payload_id,
            status=BookingIntent.Status.OPEN,
        )


def get_user_by_booking_token(token: UUID | str) -> User:
    try:
        return User.objects.get(booking_token=token)
    except User.DoesNotExist as exc:
        raise ValidationError("Token de usuario inválido.") from exc


def get_open_intent_for_user(user: User) -> BookingIntent:
    return (
        BookingIntent.objects.select_related("service", "selected_tier")
        .filter(user=user, status=BookingIntent.Status.OPEN)
        .order_by("-created_at")
        .first()
    )


def get_booking_context(token: UUID | str) -> dict:
    user = get_user_by_booking_token(token)
    intent = get_open_intent_for_user(user)
    if not intent:
        raise ValidationError("No existe una intención de reserva activa para este usuario.")

    tiers = list(
        intent.service.tiers.order_by("price").values(
            "id",
            "name",
            "price",
            "duration_minutes",
            "is_default",
        )
    )
    selected_tier_id = intent.selected_tier_id or (tiers[0]["id"] if tiers else None)

    return {
        "token": str(user.booking_token),
        "user": {
            "id": user.id,
            "name": user.name or "Cliente",
            "phone_number": user.phone_number,
        },
        "service": {
            "id": intent.service.id,
            "name": intent.service.name,
            "description": intent.service.description or "",
            "category": intent.service.category,
            "available_from": intent.service.available_from.isoformat(),
            "available_until": intent.service.available_until.isoformat() if intent.service.available_until else None,
        },
        "tiers": tiers,
        "selected_tier_id": selected_tier_id,
    }


def get_available_times(token: UUID | str, target_date: str, tier_id: int | None = None) -> dict:
    user = get_user_by_booking_token(token)
    intent = get_open_intent_for_user(user)
    if not intent:
        raise ValidationError("No existe una intención de reserva activa.")

    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    tier = intent.selected_tier
    if tier_id is not None:
        tier = ServiceTier.objects.get(id=tier_id, service=intent.service)

    if tier is None:
        raise ValidationError("No hay tier configurado para este servicio.")

    slots = get_available_slots(tier=tier, target_date=date_obj)
    return {
        "times": [slot.strftime("%H:%M") for slot in slots],
        "tier_id": tier.id,
        "date": date_obj.isoformat(),
    }


def confirm_booking(
    token: UUID | str,
    target_date: str,
    target_time: str,
    tier_id: int | None = None,
    source: str = "whatsapp",
) -> Booking:
    user = get_user_by_booking_token(token)
    intent = get_open_intent_for_user(user)
    if not intent:
        raise ValidationError("No existe una intención de reserva activa.")

    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    time_obj = datetime.strptime(target_time, "%H:%M").time()

    tier = intent.selected_tier
    if tier_id is not None:
        tier = ServiceTier.objects.get(id=tier_id, service=intent.service)
    if tier is None:
        raise ValidationError("No hay tier configurado para este servicio.")

    if not is_slot_available(tier=tier, target_date=date_obj, target_time=time_obj):
        raise ValidationError("El horario seleccionado ya no está disponible.")

    with transaction.atomic():
        booking = Booking.objects.create(
            user=user,
            service_tier=tier,
            date=date_obj,
            time=time_obj,
            status="Pendiente",
            source=source,
        )
        intent.selected_tier = tier
        intent.status = BookingIntent.Status.COMPLETED
        intent.booking = booking
        intent.save(update_fields=["selected_tier", "status", "booking", "updated_at"])

    return booking
