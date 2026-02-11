import json
import time
import uuid

from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

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


def calendar(request):
    return render(request, "calendar.html")


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

    selected_tier = next(
        (tier for tier in context["tiers"] if tier["id"] == context["selected_tier_id"]),
        None,
    )
    return render(
        request,
        "user_calendar.html",
        {
            "booking_token": context["token"],
            "service_name": context["service"]["name"],
            "service_description": context["service"]["description"],
            "tier_name": selected_tier["name"] if selected_tier else "",
            "tier_duration": selected_tier["duration_minutes"] if selected_tier else "",
            "tier_price": selected_tier["price"] if selected_tier else "",
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
