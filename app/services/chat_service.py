from datetime import timedelta

from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils import timezone

from app.models import Booking, BotFlowOption, ChatConversation, Message, Service, User
from app.services.whatsapp_client import send_text_message


WINDOW_DURATION = timedelta(hours=24)


def _broadcast_chat_event(user_id: int, event: str = "chat.updated") -> None:
    try:
        from channels.layers import get_channel_layer
    except Exception:
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        "dashboard_chats",
        {
            "type": "chat.event",
            "event": event,
            "user_id": user_id,
        },
    )


def _ensure_conversation(user: User) -> ChatConversation:
    conversation, _ = ChatConversation.objects.get_or_create(user=user)
    return conversation


def _remaining_seconds(conversation: ChatConversation) -> int:
    if not conversation.last_user_message_at:
        return 0
    expires_at = conversation.last_user_message_at + WINDOW_DURATION
    delta = expires_at - timezone.now()
    return max(int(delta.total_seconds()), 0)


def _mark_latest_booking_as_doubts(user: User) -> None:
    booking = (
        Booking.objects.filter(user=user)
        .exclude(status=Booking.Status.CANCELLED)
        .order_by("-date", "-time", "-id")
        .first()
    )
    if booking and booking.status != Booking.Status.DOUBTS:
        booking.status = Booking.Status.DOUBTS
        booking.save(update_fields=["status", "updated_at"])


def is_chat_handover_active(user: User) -> bool:
    conversation = ChatConversation.objects.filter(user=user).only("status").first()
    if not conversation:
        return False
    return conversation.status == ChatConversation.Status.PENDING


def register_user_message(user: User) -> ChatConversation | None:
    conversation = ChatConversation.objects.filter(user=user).first()
    if not conversation:
        return None
    conversation.last_user_message_at = timezone.now()
    update_fields = ["last_user_message_at", "updated_at"]
    if conversation.status == ChatConversation.Status.PENDING:
        conversation.resolved_at = None
        update_fields.append("resolved_at")
    conversation.save(update_fields=update_fields)
    _broadcast_chat_event(user.id, event="chat.message")
    return conversation


def _ensure_conversation_if_needed(user: User) -> ChatConversation:
    conversation, _ = ChatConversation.objects.get_or_create(
        user=user,
        defaults={
            "status": ChatConversation.Status.PENDING,
            "last_user_message_at": timezone.now(),
        },
    )
    return conversation


def mark_chat_needs_attention(user: User) -> ChatConversation:
    conversation = _ensure_conversation_if_needed(user)
    conversation.last_user_message_at = timezone.now()
    if conversation.status != ChatConversation.Status.PENDING:
        conversation.status = ChatConversation.Status.PENDING
        conversation.resolved_at = None
    conversation.save(update_fields=["last_user_message_at", "status", "resolved_at", "updated_at"])
    _mark_latest_booking_as_doubts(user)
    _broadcast_chat_event(user.id, event="chat.attention")
    return conversation


def mark_chat_resolved(user: User) -> ChatConversation:
    conversation = _ensure_conversation(user)
    conversation.status = ChatConversation.Status.RESOLVED
    conversation.resolved_at = timezone.now()
    conversation.save(update_fields=["status", "resolved_at", "updated_at"])
    _broadcast_chat_event(user.id, event="chat.resolved")
    return conversation


def reopen_chat(user: User) -> ChatConversation:
    conversation = _ensure_conversation(user)
    conversation.status = ChatConversation.Status.PENDING
    conversation.resolved_at = None
    conversation.save(update_fields=["status", "resolved_at", "updated_at"])
    _broadcast_chat_event(user.id, event="chat.reopened")
    return conversation


def _friendly_message_content(
    message: Message,
    option_title_map: dict[str, str],
    service_name_map: dict[str, str],
) -> str:
    raw_payload = message.raw_payload or {}
    interactive = raw_payload.get("interactive") or {}
    list_reply = interactive.get("list_reply") or {}
    button_reply = interactive.get("button_reply") or {}
    interactive_title = (list_reply.get("title") or button_reply.get("title") or "").strip()
    if interactive_title:
        return interactive_title

    payload_key = (message.payload_id or "").strip()
    if payload_key in option_title_map:
        return option_title_map[payload_key]
    if payload_key in service_name_map:
        return f"Servicio seleccionado: {service_name_map[payload_key]}"

    content = (message.content or "").strip()
    if content in option_title_map:
        return option_title_map[content]
    if content in service_name_map:
        return f"Servicio seleccionado: {service_name_map[content]}"
    if content.startswith("opt_"):
        return "Opcion seleccionada"
    if content.startswith("Service_"):
        return "Servicio seleccionado"
    return content or "(sin contenido)"


def _serialize_message(
    message: Message,
    option_title_map: dict[str, str],
    service_name_map: dict[str, str],
) -> dict:
    role = message.sender_role
    if role not in {Message.SenderRole.USER, Message.SenderRole.BOT, Message.SenderRole.AGENT}:
        if message.direction == Message.Direction.INCOMING:
            role = Message.SenderRole.USER
        else:
            role = Message.SenderRole.BOT
    return {
        "id": message.id,
        "content": _friendly_message_content(message, option_title_map, service_name_map),
        "message_type": message.message_type,
        "direction": message.direction,
        "sender_role": role,
        "created_at": message.created_at.isoformat(),
    }


def get_chat_messages(user_id: int) -> tuple[User, list[dict]]:
    user = User.objects.get(id=user_id)
    messages = list(Message.objects.filter(user=user).order_by("created_at", "id"))

    candidate_keys: set[str] = set()
    for message in messages:
        if message.payload_id:
            candidate_keys.add(message.payload_id)
        if message.content and (message.content.startswith("opt_") or message.content.startswith("Service_")):
            candidate_keys.add(message.content)

    option_title_map: dict[str, str] = {}
    service_name_map: dict[str, str] = {}
    if candidate_keys:
        option_title_map = {
            option.trigger_key: option.title
            for option in BotFlowOption.objects.filter(trigger_key__in=candidate_keys).only("trigger_key", "title")
        }
        service_name_map = {
            service.internal_code: service.name
            for service in Service.objects.filter(internal_code__in=candidate_keys).only("internal_code", "name")
            if service.internal_code
        }

    return user, [_serialize_message(message, option_title_map, service_name_map) for message in messages]


def list_chat_threads() -> dict:
    conversations = list(
        ChatConversation.objects.select_related("user")
        .order_by("status", "-updated_at", "-id")
    )
    threads: list[dict] = []
    user_ids = [conversation.user_id for conversation in conversations]
    previews = {}
    preview_option_title_map: dict[str, str] = {}
    preview_service_name_map: dict[str, str] = {}
    if user_ids:
        latest_message_ids = (
            Message.objects.filter(user_id__in=user_ids)
            .values("user_id")
            .annotate(last_id=Max("id"))
        )
        preview_map = {
            item["user_id"]: item["last_id"]
            for item in latest_message_ids
        }
        preview_messages = list(Message.objects.filter(id__in=preview_map.values()))
        previews = {item.user_id: item for item in preview_messages}
        preview_keys: set[str] = set()
        for message in preview_messages:
            if message.payload_id:
                preview_keys.add(message.payload_id)
            if message.content and (message.content.startswith("opt_") or message.content.startswith("Service_")):
                preview_keys.add(message.content)

        if preview_keys:
            preview_option_title_map = {
                option.trigger_key: option.title
                for option in BotFlowOption.objects.filter(trigger_key__in=preview_keys).only("trigger_key", "title")
            }
            preview_service_name_map = {
                service.internal_code: service.name
                for service in Service.objects.filter(internal_code__in=preview_keys).only("internal_code", "name")
                if service.internal_code
            }

    for conversation in conversations:
        preview = previews.get(conversation.user_id)
        remaining = _remaining_seconds(conversation)
        preview_content = ""
        if preview:
            preview_content = _friendly_message_content(preview, preview_option_title_map, preview_service_name_map)
        threads.append(
            {
                "user_id": conversation.user_id,
                "name": conversation.user.name or "Cliente",
                "phone_number": conversation.user.phone_number,
                "status": conversation.status,
                "status_label": conversation.get_status_display(),
                "last_message": preview_content,
                "last_message_at": preview.created_at.isoformat() if preview else None,
                "remaining_seconds": remaining,
                "window_expired": remaining == 0,
                "window_label": _format_window_label(remaining),
            }
        )

    return {
        "pending": [thread for thread in threads if thread["status"] == ChatConversation.Status.PENDING],
        "archived": [thread for thread in threads if thread["status"] == ChatConversation.Status.RESOLVED],
    }


def _format_window_label(remaining_seconds: int) -> str:
    if remaining_seconds <= 0:
        return "Ventana gratuita expirada"
    hours = remaining_seconds // 3600
    minutes = (remaining_seconds % 3600) // 60
    return f"Ventana gratuita restante: {hours}h {minutes:02d}m"


def send_agent_text_message(*, user_id: int, text: str) -> Message | None:
    user = User.objects.get(id=user_id)
    conversation = _ensure_conversation(user)
    remaining = _remaining_seconds(conversation)
    if remaining <= 0:
        raise ValidationError(
            "No se puede enviar el mensaje porque la ventana gratuita de 24 horas ha expirado."
        )

    success, error_message, sent_message = send_text_message(
        to=user.phone_number,
        text=text,
        user=user,
        sender_role=Message.SenderRole.AGENT,
    )
    if not success:
        if "24" in (error_message or "") or "window" in (error_message or "").lower():
            raise ValidationError(
                "No se puede enviar el mensaje porque la ventana gratuita de 24 horas ha expirado."
            )
        raise ValidationError(error_message or "No se pudo enviar el mensaje al usuario.")

    if conversation.status != ChatConversation.Status.PENDING:
        conversation.status = ChatConversation.Status.PENDING
        conversation.resolved_at = None
        conversation.save(update_fields=["status", "resolved_at", "updated_at"])

    _broadcast_chat_event(user.id, event="chat.message")
    return sent_message
