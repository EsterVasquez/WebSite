import json
import logging

logger = logging.getLogger("wa_bot")
err_logger = logging.getLogger("wa_bot.errors")
SEP = "-" * 70

def safe_json(obj, max_len=2500) -> str:
    """JSON bonito pero recortado para que no explote el log."""
    try:
        s = json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        s = str(obj)
    return s if len(s) <= max_len else (s[:max_len] + " ...[TRUNCATED]")

def pick_meta(data: dict) -> dict:
    """
    Extrae lo importante del webhook para log.
    Evita imprimir TODO el JSON.
    """
    try:
        entry = (data.get("entry") or [{}])[0]
        changes = (entry.get("changes") or [{}])[0]
        value = changes.get("value") or {}

        messages = value.get("messages") or []
        msg = messages[0] if messages else {}

        meta = {
            "from": msg.get("from"),
            "type": msg.get("type"),
            "wamid": msg.get("id"),
        }

        if msg.get("type") == "text":
            meta["text"] = ((msg.get("text") or {}).get("body") or "")[:120]

        if msg.get("type") == "interactive":
            interactive = msg.get("interactive") or {}
            list_reply = interactive.get("list_reply")
            button_reply = interactive.get("button_reply")
            if list_reply:
                meta["interactive_id"] = list_reply.get("id")
                meta["interactive_title"] = (list_reply.get("title") or "")[:80]
            elif button_reply:
                meta["interactive_id"] = button_reply.get("id")
                meta["interactive_title"] = (button_reply.get("title") or "")[:80]

        # contacts (si viene)
        contacts = value.get("contacts") or []
        if contacts:
            meta["wa_id"] = contacts[0].get("wa_id")
            meta["name"] = ((contacts[0].get("profile") or {}).get("name") or "")[:40]

        return meta
    except Exception:
        return {"meta_error": "could_not_parse_payload"}

def log_event(event: str, request_id: str, **fields):
    parts = [event, f"request_id={request_id}"]
    for k, v in fields.items():
        parts.append(f"{k}={v}")
    logger.info(" | ".join(parts))

def log_error(event: str, request_id: str, **fields):
    parts = [event, f"request_id={request_id}"]
    for k, v in fields.items():
        parts.append(f"{k}={v}")
    err_logger.error(" | ".join(parts))

def request_start(request_id: str, **fields):
    # fields: from, type, text, interactive_id, wa_id, name...
    details = " | ".join([f"{k}={v}" for k, v in fields.items() if v not in (None, "", [])])
    logger.info("\n" + SEP)
    logger.info(f"🚀 INICIO REQUEST | request_id={request_id}" + (f" | {details}" if details else ""))
    logger.info(SEP)

def request_end(request_id: str, ms: int | None = None, **fields):
    details = " | ".join([f"{k}={v}" for k, v in fields.items() if v not in (None, "", [])])
    extra = []
    if ms is not None:
        extra.append(f"ms={ms}")
    if details:
        extra.append(details)

    logger.info(SEP)
    logger.info(f"✅ FIN REQUEST | request_id={request_id}" + (f" | {' | '.join(extra)}" if extra else ""))
    logger.info(SEP + "\n")