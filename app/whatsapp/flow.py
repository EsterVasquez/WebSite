from dataclasses import dataclass

from app.models import Message, User
from app.services.chat_service import (
    is_chat_handover_active,
    mark_chat_needs_attention,
    register_user_message,
)
from app.services.bot_flow_service import route_with_flow_nodes
from app.services.booking_service import create_booking_intent
from app.services.catalog_service import get_service_by_code
from app.whatsapp.constants import PIXIESET_DEFAULT_LINK
from app.whatsapp.payloads import (
    booking_payload,
    quote_payload,
    text_message,
)


@dataclass
class IncomingRoutingResult:
    sender: str
    selected_key: str | None
    user: User
    payloads: list[dict]


def _extract_sender_name(value: dict) -> str | None:
    contacts = value.get("contacts") or []
    if not contacts:
        return None
    profile = contacts[0].get("profile") or {}
    return profile.get("name")


def _extract_message_selection(message: dict) -> tuple[str, str | None]:
    message_type = message.get("type")
    if message_type == "text":
        text = ((message.get("text") or {}).get("body") or "").strip()
        return text, None

    interactive = message.get("interactive") or {}
    list_reply = interactive.get("list_reply") or {}
    button_reply = interactive.get("button_reply") or {}
    payload_id = list_reply.get("id") or button_reply.get("id")
    title = list_reply.get("title") or button_reply.get("title")
    return payload_id or "", title


def _normalize_key(raw_key: str) -> str:
    key = (raw_key or "").strip()
    return key


def _get_or_create_user(sender: str, sender_name: str | None) -> User:
    defaults = {"name": sender_name or ""}
    user, _ = User.objects.get_or_create(phone_number=sender, defaults=defaults)
    if sender_name and user.name != sender_name:
        user.name = sender_name
        user.save(update_fields=["name", "updated_at"])
    return user


def _save_incoming_message(
    user: User,
    message_type: str,
    content: str,
    payload_id: str | None,
    raw_payload: dict,
) -> None:
    Message.objects.create(
        user=user,
        content=content or "",
        direction=Message.Direction.INCOMING,
        sender_role=Message.SenderRole.USER,
        message_type=message_type or "unknown",
        payload_id=payload_id or "",
        raw_payload=raw_payload,
    )
    register_user_message(user)


def _handle_service_selection(sender: str, user: User, payload_id: str, base_url: str) -> list[dict]:
    service = get_service_by_code(payload_id)
    if service is None:
        return [text_message(sender, "El servicio seleccionado no esta configurado.")]

    if user.conversation_state == User.ConversationState.QUOTE:
        link = service.quote_url or PIXIESET_DEFAULT_LINK
        return quote_payload(sender, service.name, link)

    if user.conversation_state == User.ConversationState.BOOKING:
        create_booking_intent(user=user, service=service, source_option_key=payload_id)
        booking_url = f"{base_url.rstrip('/')}/calendario/{user.booking_token}/"
        payloads = booking_payload(
            sender=sender,
            service_name=service.name,
            service_description=service.description or "Servicio fotografico personalizado.",
            booking_url=booking_url,
        )
        payloads.append(text_message(sender, booking_url))
        return payloads

    return [
        text_message(
            sender,
            "Primero elige si deseas cotizar o agendar para ayudarte con el flujo correcto.",
        )
    ]


def route_incoming_whatsapp_event(data: dict, base_url: str) -> IncomingRoutingResult | None:
    entry = (data.get("entry") or [{}])[0]
    changes = (entry.get("changes") or [{}])[0]
    value = changes.get("value") or {}

    messages = value.get("messages") or []
    if not messages:
        return None

    message = messages[0]
    sender = message["from"]
    sender_name = _extract_sender_name(value)
    message_type = message.get("type", "unknown")

    raw_key, selection_title = _extract_message_selection(message)
    selected_key = _normalize_key(raw_key)

    user = _get_or_create_user(sender=sender, sender_name=sender_name)
    _save_incoming_message(
        user=user,
        message_type=message_type,
        content=selection_title or raw_key,
        payload_id=selected_key,
        raw_payload=message,
    )

    if is_chat_handover_active(user):
        return IncomingRoutingResult(
            sender=sender,
            selected_key=selected_key,
            user=user,
            payloads=[],
        )

    node_payloads = route_with_flow_nodes(sender=sender, selected_key=selected_key, user=user, base_url=base_url)
    normalized_key = selected_key.strip().lower()
    if normalized_key in {"dudas", "dudas/otro", "duda", "otro"}:
        mark_chat_needs_attention(user)

    if node_payloads is not None:
        return IncomingRoutingResult(
            sender=sender,
            selected_key=selected_key,
            user=user,
            payloads=node_payloads,
        )

    if selected_key.startswith("Service_"):
        return IncomingRoutingResult(
            sender=sender,
            selected_key=selected_key,
            user=user,
            payloads=_handle_service_selection(
                sender=sender,
                user=user,
                payload_id=selected_key,
                base_url=base_url,
            ),
        )

    fallback_payloads = route_with_flow_nodes(
        sender=sender,
        selected_key="inicio",
        user=user,
        base_url=base_url,
    )
    if fallback_payloads:
        mark_chat_needs_attention(user)
        payloads = [text_message(sender, "No identifique tu respuesta, te comparto el menu principal.")]
        payloads.extend(fallback_payloads)
        return IncomingRoutingResult(
            sender=sender,
            selected_key=selected_key,
            user=user,
            payloads=payloads,
        )

    return IncomingRoutingResult(
        sender=sender,
        selected_key=selected_key,
        user=user,
        payloads=[text_message(sender, "No identifique tu respuesta.")],
    )
