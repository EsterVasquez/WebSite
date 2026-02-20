from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from app.models import Service, ServiceException, ServicePackage, ServiceWeeklyRange


def _next_order(queryset) -> int:
    max_order = queryset.aggregate(v=Max("order_index")).get("v") or 0
    return max_order + 10


def _is_checked(value: str | None) -> bool:
    return value in {"on", "true", "1", "yes"}


def _parse_int(value: str | None, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _find_weekly_overlap_warnings(service: Service) -> list[str]:
    warnings: list[str] = []
    for weekday, weekday_label in ServiceWeeklyRange.Weekday.choices:
        ranges = list(
            service.weekly_ranges.filter(weekday=weekday).order_by("start_time").values("start_time", "end_time")
        )
        for index, current in enumerate(ranges):
            for candidate in ranges[index + 1 :]:
                if current["start_time"] < candidate["end_time"] and candidate["start_time"] < current["end_time"]:
                    warnings.append(
                        f"Solapamiento en {weekday_label}: {current['start_time']} - {current['end_time']} "
                        f"con {candidate['start_time']} - {candidate['end_time']}."
                    )
    return warnings


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _validate_service_date_range(
    *,
    availability_type: str,
    available_from: date | None,
    available_until: date | None,
) -> str | None:
    if availability_type == Service.AvailabilityType.TEMPORARY:
        if not available_from or not available_until:
            return "Los servicios temporales requieren fecha de inicio y fecha de fin."
        if available_from > available_until:
            return "La fecha inicial no puede ser mayor a la fecha final."
    return None


def _service_context(service_id: int | None = None) -> dict:
    services = list(
        Service.objects.prefetch_related("weekly_ranges", "exceptions", "packages").order_by("name")
    )
    selected = None
    if service_id:
        selected = next((item for item in services if item.id == service_id), None)
    if selected is None and services:
        selected = services[0]

    overlap_warnings = _find_weekly_overlap_warnings(selected) if selected else []
    return {
        "services": services,
        "selected_service": selected,
        "weekday_choices": ServiceWeeklyRange.Weekday.choices,
        "availability_choices": Service.AvailabilityType.choices,
        "exception_type_choices": ServiceException.ExceptionType.choices,
        "exception_range_mode_choices": ServiceException.RangeMode.choices,
        "overlap_warnings": overlap_warnings,
    }


@login_required
def service_manager(request):
    service_id = request.GET.get("service")
    context = _service_context(_parse_int(service_id) if service_id else None)
    return render(request, "service_manager.html", context)


@login_required
@require_POST
def create_service(request):
    name = (request.POST.get("name") or "").strip()
    if not name:
        messages.error(request, "Debes indicar el nombre del servicio.")
        return redirect("service_manager")

    availability_type = request.POST.get("availability_type") or Service.AvailabilityType.PERMANENT
    available_from = _parse_date(request.POST.get("available_from"))
    available_until = _parse_date(request.POST.get("available_until"))
    error_message = _validate_service_date_range(
        availability_type=availability_type,
        available_from=available_from,
        available_until=available_until,
    )
    if error_message:
        messages.error(request, error_message)
        return redirect("service_manager")

    service = Service.objects.create(
        name=name,
        slug="",
        category=(request.POST.get("category") or "").strip(),
        description=(request.POST.get("description") or "").strip(),
        quote_url=(request.POST.get("quote_url") or "").strip(),
        availability_type=availability_type,
        available_from=available_from,
        available_until=available_until,
        default_duration_minutes=_parse_int(request.POST.get("default_duration_minutes"), 60),
        booking_interval_minutes=_parse_int(request.POST.get("booking_interval_minutes"), 20),
        is_active=_is_checked(request.POST.get("is_active")),
    )
    messages.success(request, f"Servicio '{service.name}' creado.")
    return redirect(f"/servicios-manager/?service={service.id}")


@login_required
@require_POST
def update_service(request, service_id: int):
    service = get_object_or_404(Service, id=service_id)
    availability_type = request.POST.get("availability_type") or Service.AvailabilityType.PERMANENT
    available_from = _parse_date(request.POST.get("available_from"))
    available_until = _parse_date(request.POST.get("available_until"))
    error_message = _validate_service_date_range(
        availability_type=availability_type,
        available_from=available_from,
        available_until=available_until,
    )
    if error_message:
        messages.error(request, error_message)
        return redirect(f"/servicios-manager/?service={service.id}")

    service.name = (request.POST.get("name") or service.name).strip() or service.name
    service.category = (request.POST.get("category") or "").strip()
    service.description = (request.POST.get("description") or "").strip()
    service.quote_url = (request.POST.get("quote_url") or "").strip()
    service.availability_type = availability_type
    service.available_from = available_from
    service.available_until = available_until
    service.default_duration_minutes = _parse_int(request.POST.get("default_duration_minutes"), 60)
    service.booking_interval_minutes = _parse_int(request.POST.get("booking_interval_minutes"), 20)
    service.is_active = _is_checked(request.POST.get("is_active"))
    service.save()
    messages.success(request, "Servicio actualizado.")
    return redirect(f"/servicios-manager/?service={service.id}")


@login_required
@require_POST
def delete_service(request, service_id: int):
    service = get_object_or_404(Service, id=service_id)
    service.delete()
    messages.success(request, "Servicio eliminado.")
    return redirect("service_manager")


@login_required
@require_POST
def create_weekly_range(request, service_id: int):
    service = get_object_or_404(Service, id=service_id)
    start_time = request.POST.get("start_time")
    end_time = request.POST.get("end_time")
    if not start_time or not end_time or start_time >= end_time:
        messages.error(request, "El horario semanal debe tener inicio y fin válidos.")
        return redirect(f"/servicios-manager/?service={service.id}")

    ServiceWeeklyRange.objects.create(
        service=service,
        weekday=_parse_int(request.POST.get("weekday")),
        label=(request.POST.get("label") or "").strip(),
        start_time=start_time,
        end_time=end_time,
        order_index=_next_order(service.weekly_ranges),
    )
    messages.success(request, "Bloque horario semanal agregado.")
    return redirect(f"/servicios-manager/?service={service.id}")


@login_required
@require_POST
def delete_weekly_range(request, range_id: int):
    weekly_range = get_object_or_404(ServiceWeeklyRange, id=range_id)
    service_id = weekly_range.service_id
    weekly_range.delete()
    messages.success(request, "Bloque horario eliminado.")
    return redirect(f"/servicios-manager/?service={service_id}")


@login_required
@require_POST
def update_weekly_range(request, range_id: int):
    weekly_range = get_object_or_404(ServiceWeeklyRange, id=range_id)
    start_time = request.POST.get("start_time") or weekly_range.start_time.strftime("%H:%M")
    end_time = request.POST.get("end_time") or weekly_range.end_time.strftime("%H:%M")
    if start_time >= end_time:
        messages.error(request, "El horario semanal debe tener inicio menor al fin.")
        return redirect(f"/servicios-manager/?service={weekly_range.service_id}")

    weekly_range.weekday = _parse_int(request.POST.get("weekday"), weekly_range.weekday)
    weekly_range.label = (request.POST.get("label") or "").strip()
    weekly_range.start_time = request.POST.get("start_time") or weekly_range.start_time
    weekly_range.end_time = request.POST.get("end_time") or weekly_range.end_time
    weekly_range.save()
    messages.success(request, "Bloque horario actualizado.")
    return redirect(f"/servicios-manager/?service={weekly_range.service_id}")


@login_required
@require_POST
def create_exception(request, service_id: int):
    service = get_object_or_404(Service, id=service_id)
    exception_type = request.POST.get("exception_type") or ServiceException.ExceptionType.CLOSED
    start_time = request.POST.get("start_time") or None
    end_time = request.POST.get("end_time") or None
    if exception_type == ServiceException.ExceptionType.SPECIAL_RANGE:
        if not start_time or not end_time or start_time >= end_time:
            messages.error(request, "La excepción de horario especial requiere inicio y fin válidos.")
            return redirect(f"/servicios-manager/?service={service.id}")

    ServiceException.objects.create(
        service=service,
        date=request.POST.get("date"),
        exception_type=exception_type,
        range_mode=request.POST.get("range_mode") or ServiceException.RangeMode.REPLACE,
        start_time=start_time,
        end_time=end_time,
        max_bookings=_parse_int(request.POST.get("max_bookings")) or None,
        notes=(request.POST.get("notes") or "").strip(),
        is_active=True,
    )
    messages.success(request, "Excepción creada.")
    return redirect(f"/servicios-manager/?service={service.id}")


@login_required
@require_POST
def delete_exception(request, exception_id: int):
    exception = get_object_or_404(ServiceException, id=exception_id)
    service_id = exception.service_id
    exception.delete()
    messages.success(request, "Excepción eliminada.")
    return redirect(f"/servicios-manager/?service={service_id}")


@login_required
@require_POST
def update_exception(request, exception_id: int):
    exception = get_object_or_404(ServiceException, id=exception_id)
    new_exception_type = request.POST.get("exception_type") or exception.exception_type
    start_time = request.POST.get("start_time") or None
    end_time = request.POST.get("end_time") or None
    if new_exception_type == ServiceException.ExceptionType.SPECIAL_RANGE:
        if not start_time or not end_time or start_time >= end_time:
            messages.error(request, "La excepción de horario especial requiere inicio y fin válidos.")
            return redirect(f"/servicios-manager/?service={exception.service_id}")

    exception.date = request.POST.get("date") or exception.date
    exception.exception_type = new_exception_type
    exception.range_mode = request.POST.get("range_mode") or exception.range_mode
    exception.start_time = start_time
    exception.end_time = end_time
    exception.max_bookings = _parse_int(request.POST.get("max_bookings")) or None
    exception.notes = (request.POST.get("notes") or "").strip()
    exception.save()
    messages.success(request, "Excepción actualizada.")
    return redirect(f"/servicios-manager/?service={exception.service_id}")


@login_required
@require_POST
def create_package(request, service_id: int):
    service = get_object_or_404(Service, id=service_id)
    name = (request.POST.get("name") or "").strip()
    if not name:
        messages.error(request, "El paquete debe tener un nombre.")
        return redirect(f"/servicios-manager/?service={service.id}")

    available_from = _parse_date(request.POST.get("available_from"))
    available_until = _parse_date(request.POST.get("available_until"))
    if available_from and available_until and available_from > available_until:
        messages.error(request, "La fecha inicial del paquete no puede ser mayor a la final.")
        return redirect(f"/servicios-manager/?service={service.id}")

    price = _parse_float(request.POST.get("price"), 0)
    deposit = _parse_float(request.POST.get("deposit_required"), 0)
    if price < 0 or deposit < 0:
        messages.error(request, "Precio y anticipo deben ser valores iguales o mayores a cero.")
        return redirect(f"/servicios-manager/?service={service.id}")

    is_default = _is_checked(request.POST.get("is_default"))
    package = ServicePackage.objects.create(
        service=service,
        name=name,
        description=(request.POST.get("description") or "").strip(),
        price=price,
        deposit_required=deposit,
        duration_minutes=_parse_int(request.POST.get("duration_minutes")) or None,
        available_from=available_from,
        available_until=available_until,
        max_bookings=_parse_int(request.POST.get("max_bookings")) or None,
        is_default=is_default,
        is_active=_is_checked(request.POST.get("is_active")),
        order_index=_next_order(service.packages),
    )
    if is_default:
        service.packages.exclude(id=package.id).update(is_default=False)
    messages.success(request, "Paquete agregado.")
    return redirect(f"/servicios-manager/?service={service.id}")


@login_required
@require_POST
def delete_package(request, package_id: int):
    package = get_object_or_404(ServicePackage, id=package_id)
    service_id = package.service_id
    package.delete()
    messages.success(request, "Paquete eliminado.")
    return redirect(f"/servicios-manager/?service={service_id}")


@login_required
@require_POST
def update_package(request, package_id: int):
    package = get_object_or_404(ServicePackage, id=package_id)
    available_from = _parse_date(request.POST.get("available_from"))
    available_until = _parse_date(request.POST.get("available_until"))
    if available_from and available_until and available_from > available_until:
        messages.error(request, "La fecha inicial del paquete no puede ser mayor a la final.")
        return redirect(f"/servicios-manager/?service={package.service_id}")

    price = _parse_float(request.POST.get("price"), float(package.price))
    deposit = _parse_float(request.POST.get("deposit_required"), float(package.deposit_required))
    if price < 0 or deposit < 0:
        messages.error(request, "Precio y anticipo deben ser valores iguales o mayores a cero.")
        return redirect(f"/servicios-manager/?service={package.service_id}")

    package.name = (request.POST.get("name") or package.name).strip() or package.name
    package.description = (request.POST.get("description") or "").strip()
    package.price = price
    package.deposit_required = deposit
    package.duration_minutes = _parse_int(request.POST.get("duration_minutes")) or None
    package.available_from = available_from
    package.available_until = available_until
    package.max_bookings = _parse_int(request.POST.get("max_bookings")) or None
    package.is_default = _is_checked(request.POST.get("is_default"))
    package.is_active = _is_checked(request.POST.get("is_active"))
    package.save()
    if package.is_default:
        package.service.packages.exclude(id=package.id).update(is_default=False)
    messages.success(request, "Paquete actualizado.")
    return redirect(f"/servicios-manager/?service={package.service_id}")
