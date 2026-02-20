import json
import time
import uuid

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from app.models import Booking
from app.services.booking_service import get_booking_context
from app.services.whatsapp_client import send_messages
from app.wa_logs import log_error, log_event, pick_meta, request_end, request_start
from app.whatsapp.flow import route_incoming_whatsapp_event


@csrf_exempt
def webhook(request):
    started_at = time.perf_counter()
    request_id = uuid.uuid4().hex[:10]

    if request.method != "POST":
        log_event("WEBHOOK_METHOD_NOT_ALLOWED", request_id, method=request.method)
        return HttpResponse("Método no permitido", status=405)

    try:
        data = json.loads(request.body)

        value = ((data.get("entry") or [{}])[0].get("changes") or [{}])[0].get("value") or {}
        messages = value.get("messages")
        if not messages:
            return HttpResponse("EVENT_RECEIVED", status=200)

        meta = pick_meta(data)
        request_start(request_id, **meta)
        log_event("INCOMING", request_id, **meta)

        base_url = f"{request.scheme}://{request.get_host()}"
        result = route_incoming_whatsapp_event(data=data, base_url=base_url)
        if result is None:
            return HttpResponse("EVENT_RECEIVED", status=200)

        log_event(
            "ROUTE",
            request_id,
            key=result.selected_key,
            payload_count=len(result.payloads),
            sender=result.sender,
        )
        send_messages(payloads=result.payloads, request_id=request_id, user=result.user)

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        request_end(request_id, ms=elapsed_ms, sent=len(result.payloads))
    except Exception as exc:
        log_error("WEBHOOK_EXCEPTION", request_id, err=str(exc))
        try:
            raw = request.body.decode("utf-8", errors="ignore")
            log_error("RAW_BODY", request_id, body=raw[:2000])
        except Exception:
            pass

    return HttpResponse("EVENT_RECEIVED", status=200)


@login_required
def calendar(request):
    return render(request, "calendar.html")


@login_required
def calendar_view(request):
    return render(request, "calendar_view.html")


@login_required
def manual_booking(request):
    return render(request, "manual_booking.html", {"booking_statuses": Booking.Status.choices})


@login_required
def chats(request):
    return render(request, "chats.html")


def public_calendar_entry(request):
    return render(
        request,
        "user_calendar.html",
        {
            "booking_error": "Esta liga requiere un token único. Abre el enlace enviado por WhatsApp para continuar.",
            "booking_token": "",
        },
    )


def user_calendar(request, token):
    try:
        context = get_booking_context(token)
    except ValidationError as exc:
        return render(
            request,
            "user_calendar.html",
            {
                "booking_token": str(token),
                "booking_error": str(exc),
            },
        )

    selected_package = next(
        (item for item in context["packages"] if item["id"] == context["selected_package_id"]),
        None,
    )
    return render(
        request,
        "user_calendar.html",
        {
            "booking_token": context["token"],
            "service_name": context["service"]["name"],
            "service_description": context["service"]["description"],
            "package_name": selected_package["name"] if selected_package else "",
            "package_duration": selected_package["duration_minutes"] if selected_package else "",
            "package_price": selected_package["price"] if selected_package else "",
            "package_deposit": selected_package["deposit_required"] if selected_package else "",
        },
    )


def auth_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("calendar")
        return render(
            request,
            "login.html",
            {"error": "Usuario o contraseña incorrectos"},
        )
    return render(request, "login.html")
