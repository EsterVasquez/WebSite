from datetime import datetime
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from app.models import Booking, BookingIntent, Service, ServicePackage, User
from app.services.scheduling import get_available_slots, is_slot_available


def _default_package(service: Service) -> ServicePackage | None:
    return (
        service.packages.filter(is_active=True, is_default=True).order_by("order_index", "id").first()
        or service.packages.filter(is_active=True).order_by("order_index", "id").first()
    )


def _validate_date_in_service_range(service: Service, date_obj) -> None:
    if service.available_from and date_obj < service.available_from:
        raise ValidationError("La fecha seleccionada es anterior al inicio de disponibilidad del servicio.")
    if service.available_until and date_obj > service.available_until:
        raise ValidationError("La fecha seleccionada está fuera del rango de disponibilidad del servicio.")


def _validate_date_in_package_range(package: ServicePackage | None, date_obj) -> None:
    if not package:
        return
    if package.available_from and date_obj < package.available_from:
        raise ValidationError("El paquete seleccionado aún no está disponible en esa fecha.")
    if package.available_until and date_obj > package.available_until:
        raise ValidationError("El paquete seleccionado ya no está disponible en esa fecha.")


def create_booking_intent(
    *,
    user: User,
    service: Service,
    source_option_key: str = "",
    package: ServicePackage | None = None,
) -> BookingIntent:
    selected_package = package or _default_package(service)

    with transaction.atomic():
        BookingIntent.objects.filter(user=user, status=BookingIntent.Status.OPEN).update(
            status=BookingIntent.Status.CANCELLED
        )
        return BookingIntent.objects.create(
            user=user,
            service=service,
            selected_package=selected_package,
            source_option_key=source_option_key,
            status=BookingIntent.Status.OPEN,
        )


def get_user_by_booking_token(token: UUID | str) -> User:
    try:
        return User.objects.get(booking_token=token)
    except User.DoesNotExist as exc:
        raise ValidationError("Token de usuario inválido.") from exc


def get_open_intent_for_user(user: User) -> BookingIntent | None:
    return (
        BookingIntent.objects.select_related("service", "selected_package")
        .filter(user=user, status=BookingIntent.Status.OPEN)
        .order_by("-created_at")
        .first()
    )


def get_booking_context(token: UUID | str) -> dict:
    user = get_user_by_booking_token(token)
    intent = get_open_intent_for_user(user)
    if not intent:
        raise ValidationError("No existe una solicitud de reserva activa para este usuario.")

    packages = list(
        intent.service.packages.filter(is_active=True).order_by("order_index", "id").values(
            "id",
            "name",
            "description",
            "price",
            "deposit_required",
            "duration_minutes",
            "available_from",
            "available_until",
            "is_default",
        )
    )

    selected_package_id = intent.selected_package_id or (packages[0]["id"] if packages else None)
    service_min_date = intent.service.available_from or timezone.localdate()
    if service_min_date < timezone.localdate():
        service_min_date = timezone.localdate()
    service_max_date = intent.service.available_until

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
            "description": intent.service.description,
            "category": intent.service.category,
            "availability_type": intent.service.availability_type,
            "available_from": intent.service.available_from.isoformat() if intent.service.available_from else None,
            "available_until": intent.service.available_until.isoformat() if intent.service.available_until else None,
            "min_booking_date": service_min_date.isoformat(),
            "max_booking_date": service_max_date.isoformat() if service_max_date else None,
            "booking_interval_minutes": intent.service.booking_interval_minutes,
            "default_duration_minutes": intent.service.default_duration_minutes,
        },
        "packages": packages,
        "selected_package_id": selected_package_id,
    }


def get_available_times(token: UUID | str, target_date: str, package_id: int | None = None) -> dict:
    user = get_user_by_booking_token(token)
    intent = get_open_intent_for_user(user)
    if not intent:
        raise ValidationError("No existe una solicitud de reserva activa.")

    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    package = intent.selected_package
    if package_id is not None:
        package = ServicePackage.objects.get(id=package_id, service=intent.service, is_active=True)

    _validate_date_in_service_range(intent.service, date_obj)
    _validate_date_in_package_range(package, date_obj)

    duration = package.duration_minutes if package and package.duration_minutes else intent.service.default_duration_minutes
    times = get_available_slots(
        service=intent.service,
        target_date=date_obj,
        duration_minutes=duration,
        booking_interval_minutes=intent.service.booking_interval_minutes,
        package=package,
    )
    return {
        "times": [slot.strftime("%H:%M") for slot in times],
        "date": date_obj.isoformat(),
        "package_id": package.id if package else None,
    }


def confirm_booking(
    *,
    token: UUID | str,
    target_date: str,
    target_time: str,
    package_id: int | None = None,
    customer_name: str = "",
    customer_phone: str = "",
    customer_notes: str = "",
    source: str = Booking.Source.WHATSAPP,
) -> Booking:
    user = get_user_by_booking_token(token)
    intent = get_open_intent_for_user(user)
    if not intent:
        raise ValidationError("No existe una solicitud de reserva activa.")

    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    time_obj = datetime.strptime(target_time, "%H:%M").time()
    package = intent.selected_package
    if package_id is not None:
        package = ServicePackage.objects.get(id=package_id, service=intent.service, is_active=True)

    if not (customer_name or user.name):
        raise ValidationError("El nombre del cliente es obligatorio para confirmar la cita.")
    if not (customer_phone or user.phone_number):
        raise ValidationError("El teléfono del cliente es obligatorio para confirmar la cita.")

    _validate_date_in_service_range(intent.service, date_obj)
    _validate_date_in_package_range(package, date_obj)

    duration = package.duration_minutes if package and package.duration_minutes else intent.service.default_duration_minutes
    available = is_slot_available(
        service=intent.service,
        target_date=date_obj,
        target_time=time_obj,
        duration_minutes=duration,
        booking_interval_minutes=intent.service.booking_interval_minutes,
        package=package,
    )
    if not available:
        raise ValidationError("El horario seleccionado ya no está disponible.")

    total_price = package.price if package else 0
    deposit_amount = package.deposit_required if package else 0

    with transaction.atomic():
        booking = Booking.objects.create(
            user=user,
            service=intent.service,
            package=package,
            customer_name=customer_name or user.name,
            customer_phone=customer_phone or user.phone_number,
            customer_notes=customer_notes,
            date=date_obj,
            time=time_obj,
            duration_minutes=duration,
            total_price=total_price,
            deposit_amount=deposit_amount,
            status=Booking.Status.PENDING,
            source=source,
        )

        intent.selected_package = package
        intent.status = BookingIntent.Status.COMPLETED
        intent.booking = booking
        intent.save(update_fields=["selected_package", "status", "booking", "updated_at"])

    return booking


def get_available_times_for_manual_booking(
    *,
    service: Service,
    target_date: str,
    package: ServicePackage | None,
) -> dict:
    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    _validate_date_in_service_range(service, date_obj)
    _validate_date_in_package_range(package, date_obj)

    duration = package.duration_minutes if package and package.duration_minutes else service.default_duration_minutes
    slots = get_available_slots(
        service=service,
        target_date=date_obj,
        duration_minutes=duration,
        booking_interval_minutes=service.booking_interval_minutes,
        package=package,
    )
    return {"times": [slot.strftime("%H:%M") for slot in slots], "date": date_obj.isoformat()}


def create_manual_booking(
    *,
    user: User,
    service: Service,
    package: ServicePackage | None,
    target_date: str,
    target_time: str,
    customer_name: str,
    customer_phone: str,
    customer_notes: str,
    deposit_amount: float,
    status: str,
) -> Booking:
    date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    time_obj = datetime.strptime(target_time, "%H:%M").time()
    _validate_date_in_service_range(service, date_obj)
    _validate_date_in_package_range(package, date_obj)

    duration = package.duration_minutes if package and package.duration_minutes else service.default_duration_minutes
    available = is_slot_available(
        service=service,
        target_date=date_obj,
        target_time=time_obj,
        duration_minutes=duration,
        booking_interval_minutes=service.booking_interval_minutes,
        package=package,
    )
    if not available:
        raise ValidationError("El horario seleccionado no está disponible para este servicio.")

    valid_statuses = {choice[0] for choice in Booking.Status.choices}
    if status not in valid_statuses:
        raise ValidationError("Estado de reservación inválido.")

    total_price = float(package.price) if package else 0
    if deposit_amount < 0:
        raise ValidationError("El anticipo no puede ser menor a cero.")
    if total_price and deposit_amount > total_price:
        raise ValidationError("El anticipo no puede ser mayor al precio del paquete.")

    booking = Booking.objects.create(
        user=user,
        service=service,
        package=package,
        customer_name=customer_name.strip(),
        customer_phone=customer_phone.strip(),
        customer_notes=customer_notes.strip(),
        date=date_obj,
        time=time_obj,
        duration_minutes=duration,
        total_price=total_price,
        deposit_amount=deposit_amount,
        status=status,
        source=Booking.Source.DASHBOARD,
    )
    return booking
