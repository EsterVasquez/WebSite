import logging
import os
import time

import requests

from app.models import Message, User
from app.wa_logs import log_error, log_event, safe_json


WHATSAPP_TOKEN = os.environ.get("W_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json",
}


def summarize_outgoing(payload: dict) -> str:
    payload_type = payload.get("type")
    target = payload.get("to")

    if payload_type == "text":
        body = (payload.get("text") or {}).get("body", "")
        return f"type=text to={target} len={len(body)}"

    if payload_type == "interactive":
        interactive_type = (payload.get("interactive") or {}).get("type")
        return f"type=interactive({interactive_type}) to={target}"

    return f"type={payload_type} to={target}"


def _payload_content(payload: dict) -> tuple[str, str]:
    payload_type = payload.get("type", "unknown")
    if payload_type == "text":
        return payload_type, (payload.get("text") or {}).get("body", "")

    if payload_type == "interactive":
        body = ((payload.get("interactive") or {}).get("body") or {}).get("text", "")
        return payload_type, body or "Mensaje interactivo"

    return payload_type, "Mensaje saliente"


def _save_outgoing(user: User | None, payload: dict) -> None:
    if user is None:
        return
    message_type, content = _payload_content(payload)
    Message.objects.create(
        user=user,
        content=content,
        direction=Message.Direction.OUTGOING,
        message_type=message_type,
        raw_payload=payload,
    )


def send_messages(payloads: list[dict], request_id: str, user: User | None = None) -> None:
    payload_logger = logging.getLogger("wa_payloads")
    for index, payload in enumerate(payloads, start=1):
        log_event("OUTGOING_SEND", request_id, n=f"{index}/{len(payloads)}", summary=summarize_outgoing(payload))
        payload_logger.debug("OUTGOING_PAYLOAD | request_id=%s\n%s", request_id, safe_json(payload, max_len=20000))
        _save_outgoing(user, payload)
        t0 = time.time()
        try:
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=15)
            elapsed_ms = int((time.time() - t0) * 1000)
            if response.ok:
                log_event("OUTGOING_OK", request_id, status=response.status_code, ms=elapsed_ms)
            else:
                log_error(
                    "OUTGOING_FAIL",
                    request_id,
                    status=response.status_code,
                    ms=elapsed_ms,
                    resp=response.text[:500].replace("\n", " "),
                )
        except requests.RequestException as exc:
            log_error("OUTGOING_EXCEPTION", request_id, err=str(exc))
