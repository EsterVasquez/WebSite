import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from app.services.booking_service import confirm_booking, get_available_times, get_booking_context
from app.services.dashboard_service import list_dashboard_bookings


@require_GET
def dashboard_bookings_api(request):
    return JsonResponse({"bookings": list_dashboard_bookings()})


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
    tier_id_raw = request.GET.get("tier_id")
    if not target_date:
        return JsonResponse({"error": "Parámetro 'date' es obligatorio (YYYY-MM-DD)."}, status=400)

    tier_id = None
    if tier_id_raw:
        try:
            tier_id = int(tier_id_raw)
        except ValueError:
            return JsonResponse({"error": "tier_id inválido."}, status=400)

    try:
        data = get_available_times(token=token, target_date=target_date, tier_id=tier_id)
    except (ValidationError, ValueError) as exc:
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
    tier_id = payload.get("tier_id")

    if not target_date or not target_time:
        return JsonResponse({"error": "Los campos 'date' y 'time' son obligatorios."}, status=400)

    try:
        booking = confirm_booking(
            token=token,
            target_date=target_date,
            target_time=target_time,
            tier_id=tier_id,
            source="whatsapp",
        )
    except (ValidationError, ValueError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "booking": {
                "id": booking.id,
                "date": booking.date.isoformat(),
                "time": booking.time.strftime("%H:%M"),
                "status": booking.status,
            },
        }
    )
