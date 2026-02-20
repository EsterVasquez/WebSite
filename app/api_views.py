import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from app.models import Booking, Service, ServicePackage, User
from app.services.booking_service import (
    confirm_booking,
    create_manual_booking,
    get_available_times,
    get_available_times_for_manual_booking,
    get_booking_context,
)
from app.services.dashboard_service import (
    list_booking_events,
    list_dashboard_bookings,
    update_booking_status,
)


def _require_authenticated(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Debes iniciar sesión para acceder a este recurso."}, status=401)
    return None


@require_GET
def dashboard_bookings_api(request):
    unauthorized = _require_authenticated(request)
    if unauthorized:
        return unauthorized
    return JsonResponse({"bookings": list_dashboard_bookings()})


@require_GET
def dashboard_bookings_events_api(request):
    unauthorized = _require_authenticated(request)
    if unauthorized:
        return unauthorized
    return JsonResponse({"events": list_booking_events()})


@require_GET
def calendar_context_api(request, token):
    try:
        context = get_booking_context(token)
    except ValidationError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(context)


@require_GET
def available_times_api(request, token):
    target_date = request.GET.get("date")
    package_id_raw = request.GET.get("package_id")
    if not target_date:
        return JsonResponse({"error": "Parametro 'date' es obligatorio (YYYY-MM-DD)."}, status=400)

    package_id = None
    if package_id_raw:
        try:
            package_id = int(package_id_raw)
        except ValueError:
            return JsonResponse({"error": "package_id invalido."}, status=400)

    try:
        data = get_available_times(token=token, target_date=target_date, package_id=package_id)
    except (ValidationError, ValueError, ServicePackage.DoesNotExist) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(data)


@csrf_exempt
def confirm_booking_api(request, token):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido, usa POST."}, status=405)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido."}, status=400)

    target_date = payload.get("date")
    target_time = payload.get("time")
    package_id = payload.get("package_id")
    customer_name = payload.get("customer_name") or ""
    customer_phone = payload.get("customer_phone") or ""
    customer_notes = payload.get("customer_notes") or ""

    if not target_date or not target_time:
        return JsonResponse({"error": "Los campos 'date' y 'time' son obligatorios."}, status=400)

    try:
        booking = confirm_booking(
            token=token,
            target_date=target_date,
            target_time=target_time,
            package_id=package_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_notes=customer_notes,
            source=Booking.Source.WHATSAPP,
        )
    except (ValidationError, ValueError, ServicePackage.DoesNotExist) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "booking": {
                "id": booking.id,
                "date": booking.date.isoformat(),
                "time": booking.time.strftime("%H:%M"),
                "status": booking.get_status_display(),
            },
        }
    )


@csrf_exempt
def dashboard_booking_status_api(request, booking_id: int):
    unauthorized = _require_authenticated(request)
    if unauthorized:
        return unauthorized
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido, usa POST."}, status=405)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido."}, status=400)

    status_code = payload.get("status")
    if not status_code:
        return JsonResponse({"error": "El campo 'status' es obligatorio."}, status=400)

    try:
        booking = update_booking_status(booking_id=booking_id, status_code=status_code)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Booking.DoesNotExist:
        return JsonResponse({"error": "Reservación no encontrada."}, status=404)

    return JsonResponse(
        {
            "ok": True,
            "booking": {
                "id": booking.id,
                "status": booking.get_status_display(),
                "status_code": booking.status,
            },
        }
    )


@require_GET
def dashboard_services_api(request):
    unauthorized = _require_authenticated(request)
    if unauthorized:
        return unauthorized

    services = Service.objects.filter(is_active=True).prefetch_related("packages").order_by("name")
    payload = []
    for service in services:
        payload.append(
            {
                "id": service.id,
                "name": service.name,
                "availability_type": service.availability_type,
                "available_from": service.available_from.isoformat() if service.available_from else None,
                "available_until": service.available_until.isoformat() if service.available_until else None,
                "default_duration_minutes": service.default_duration_minutes,
                "booking_interval_minutes": service.booking_interval_minutes,
                "packages": [
                    {
                        "id": package.id,
                        "name": package.name,
                        "price": float(package.price),
                        "deposit_required": float(package.deposit_required),
                        "duration_minutes": package.duration_minutes,
                        "available_from": package.available_from.isoformat() if package.available_from else None,
                        "available_until": package.available_until.isoformat() if package.available_until else None,
                        "is_default": package.is_default,
                    }
                    for package in service.packages.filter(is_active=True).order_by("order_index", "id")
                ],
            }
        )
    return JsonResponse({"services": payload})


@require_GET
def dashboard_manual_available_times_api(request):
    unauthorized = _require_authenticated(request)
    if unauthorized:
        return unauthorized

    service_id = request.GET.get("service_id")
    target_date = request.GET.get("date")
    package_id = request.GET.get("package_id")
    if not service_id or not target_date:
        return JsonResponse({"error": "Debes enviar service_id y date."}, status=400)

    try:
        service = Service.objects.get(id=int(service_id), is_active=True)
    except (ValueError, Service.DoesNotExist):
        return JsonResponse({"error": "Servicio inválido."}, status=400)

    package = None
    if package_id:
        try:
            package = ServicePackage.objects.get(id=int(package_id), service=service, is_active=True)
        except (ValueError, ServicePackage.DoesNotExist):
            return JsonResponse({"error": "Paquete inválido para el servicio seleccionado."}, status=400)

    try:
        data = get_available_times_for_manual_booking(service=service, target_date=target_date, package=package)
    except (ValidationError, ValueError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(data)


@csrf_exempt
def dashboard_manual_booking_create_api(request):
    unauthorized = _require_authenticated(request)
    if unauthorized:
        return unauthorized
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido, usa POST."}, status=405)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido."}, status=400)

    required = ["service_id", "date", "time", "customer_name", "customer_phone", "status"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return JsonResponse({"error": f"Faltan campos obligatorios: {', '.join(missing)}."}, status=400)

    try:
        service = Service.objects.get(id=int(payload["service_id"]), is_active=True)
    except (ValueError, Service.DoesNotExist):
        return JsonResponse({"error": "Servicio inválido."}, status=400)

    package = None
    if payload.get("package_id"):
        try:
            package = ServicePackage.objects.get(
                id=int(payload["package_id"]),
                service=service,
                is_active=True,
            )
        except (ValueError, ServicePackage.DoesNotExist):
            return JsonResponse({"error": "Paquete inválido para el servicio seleccionado."}, status=400)

    customer_phone = str(payload.get("customer_phone", "")).strip()
    customer_name = str(payload.get("customer_name", "")).strip()
    customer_notes = str(payload.get("customer_notes", "")).strip()
    deposit_amount_raw = payload.get("deposit_amount", 0)
    try:
        deposit_amount = float(deposit_amount_raw or 0)
    except (TypeError, ValueError):
        return JsonResponse({"error": "El anticipo debe ser numérico."}, status=400)

    user = User.objects.filter(phone_number=customer_phone).first()
    if not user:
        user = User.objects.create(phone_number=customer_phone, name=customer_name)
    elif customer_name and user.name != customer_name:
        user.name = customer_name
        user.save(update_fields=["name", "updated_at"])

    try:
        booking = create_manual_booking(
            user=user,
            service=service,
            package=package,
            target_date=str(payload["date"]),
            target_time=str(payload["time"]),
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_notes=customer_notes,
            deposit_amount=deposit_amount,
            status=str(payload["status"]),
        )
    except (ValidationError, ValueError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "booking": {
                "id": booking.id,
                "status": booking.get_status_display(),
                "date": booking.date.isoformat(),
                "time": booking.time.strftime("%H:%M"),
            },
        }
    )
