from collections import OrderedDict
from typing import Iterable

from django.db import transaction

from app.models import BotFlow, BotFlowNode, BotFlowOption, User
from app.services.booking_service import create_booking_intent
from app.services.catalog_service import ensure_base_services
from app.services.chat_service import mark_chat_needs_attention
from app.whatsapp.constants import (
    CATEGORY_TO_SERVICES,
    DOUBTS_MESSAGE,
    MAIN_MENU_ROWS,
    PIXIESET_DEFAULT_LINK,
    SERVICE_CATEGORY_ROWS,
)
from app.whatsapp.payloads import (
    booking_payload,
    interactive_cta_url_message,
    interactive_list_message,
    quote_payload,
    text_message,
)


def _group_rows(options: Iterable[BotFlowOption]) -> list[dict]:
    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for option in options:
        grouped.setdefault("Opciones", [])
        grouped["Opciones"].append(
            {
                "id": option.trigger_key,
                "title": option.title,
                "description": option.description or "",
            }
        )
    return [{"title": section, "rows": rows} for section, rows in grouped.items()]


def _render_node_payloads(sender: str, node: BotFlowNode) -> list[dict]:
    payloads: list[dict] = []
    if node.message_text.strip():
        payloads.append(text_message(sender, node.message_text))

    if node.interaction_type == BotFlowNode.InteractionType.OPTION_LIST:
        options = list(node.options.filter(is_active=True).order_by("order_index", "id"))
        if options:
            payloads.append(
                interactive_list_message(
                    sender,
                    node.menu_title or node.title,
                    node.menu_description or "Selecciona una opcion.",
                    _group_rows(options),
                    button_text=node.menu_button_text or "Ver opciones",
                )
            )

    if node.interaction_type == BotFlowNode.InteractionType.URL_BUTTON and node.link_button_url:
        payloads.append(
            interactive_cta_url_message(
                sender,
                node.menu_description or "Haz clic en el boton para continuar.",
                node.link_button_text or "Abrir enlace",
                node.link_button_url,
            )
        )

    return payloads


def get_active_flow() -> BotFlow | None:
    return (
        BotFlow.objects.filter(is_active=True, is_published=True)
        .order_by("-updated_at", "id")
        .first()
    )


def get_start_node(flow: BotFlow) -> BotFlowNode | None:
    return (
        flow.nodes.filter(is_active=True, is_start=True).order_by("order_index", "id").first()
        or flow.nodes.filter(is_active=True).order_by("order_index", "id").first()
    )


def ensure_default_bot_flow_seeded() -> BotFlow:
    flow, _ = BotFlow.objects.get_or_create(
        slug="flujo-principal",
        defaults={
            "name": "Flujo principal WhatsApp",
            "description": "Flujo principal del bot de fotografia.",
            "is_active": True,
            "is_published": True,
        },
    )
    services = {service.internal_code: service for service in ensure_base_services() if service.internal_code}

    with transaction.atomic():
        if flow.nodes.exists():
            return flow

        start = BotFlowNode.objects.create(
            flow=flow,
            key="inicio",
            title="Bienvenida",
            message_text=(
                "Hola. Gracias por comunicarte a Jonathan CA Photography.\n"
                "Soy el asistente virtual y te ayudare con cotizaciones y agenda."
            ),
            interaction_type=BotFlowNode.InteractionType.OPTION_LIST,
            menu_title="¿Por que te comunicas con nosotros?",
            menu_description="Selecciona una opcion para continuar.",
            menu_button_text="Opciones",
            is_start=True,
            order_index=10,
        )
        booking_categories = BotFlowNode.objects.create(
            flow=flow,
            key="categorias_agendar",
            title="Categorias para agendar",
            interaction_type=BotFlowNode.InteractionType.OPTION_LIST,
            menu_title="Tipos de servicios",
            menu_description="Selecciona una categoria.",
            menu_button_text="Categorias",
            order_index=20,
        )
        quote_categories = BotFlowNode.objects.create(
            flow=flow,
            key="categorias_cotizar",
            title="Categorias para cotizar",
            interaction_type=BotFlowNode.InteractionType.OPTION_LIST,
            menu_title="Tipos de servicios",
            menu_description="Selecciona una categoria.",
            menu_button_text="Categorias",
            order_index=30,
        )
        events_booking = BotFlowNode.objects.create(
            flow=flow,
            key="servicios_eventos_agendar",
            title="Eventos para agendar",
            interaction_type=BotFlowNode.InteractionType.OPTION_LIST,
            menu_title="Eventos sociales",
            menu_description="Selecciona el servicio que te interesa.",
            menu_button_text="Servicios",
            order_index=40,
        )
        sessions_booking = BotFlowNode.objects.create(
            flow=flow,
            key="servicios_sesiones_agendar",
            title="Sesiones para agendar",
            interaction_type=BotFlowNode.InteractionType.OPTION_LIST,
            menu_title="Sesiones de estudio",
            menu_description="Selecciona el servicio que te interesa.",
            menu_button_text="Servicios",
            order_index=50,
        )
        thematic_booking = BotFlowNode.objects.create(
            flow=flow,
            key="servicios_tematicos_agendar",
            title="Tematicos para agendar",
            interaction_type=BotFlowNode.InteractionType.OPTION_LIST,
            menu_title="Sesiones tematicas",
            menu_description="Selecciona el servicio que te interesa.",
            menu_button_text="Servicios",
            order_index=60,
        )
        events_quote = BotFlowNode.objects.create(
            flow=flow,
            key="servicios_eventos_cotizar",
            title="Eventos para cotizar",
            interaction_type=BotFlowNode.InteractionType.OPTION_LIST,
            menu_title="Eventos sociales",
            menu_description="Selecciona el servicio que te interesa.",
            menu_button_text="Servicios",
            order_index=70,
        )
        sessions_quote = BotFlowNode.objects.create(
            flow=flow,
            key="servicios_sesiones_cotizar",
            title="Sesiones para cotizar",
            interaction_type=BotFlowNode.InteractionType.OPTION_LIST,
            menu_title="Sesiones de estudio",
            menu_description="Selecciona el servicio que te interesa.",
            menu_button_text="Servicios",
            order_index=80,
        )
        thematic_quote = BotFlowNode.objects.create(
            flow=flow,
            key="servicios_tematicos_cotizar",
            title="Tematicos para cotizar",
            interaction_type=BotFlowNode.InteractionType.OPTION_LIST,
            menu_title="Sesiones tematicas",
            menu_description="Selecciona el servicio que te interesa.",
            menu_button_text="Servicios",
            order_index=90,
        )
        delivery = BotFlowNode.objects.create(
            flow=flow,
            key="entrega",
            title="Entrega",
            message_text=(
                "Nuestro tiempo de entrega depende del servicio. "
                "Si ya tienes reserva comparte tu nombre para revisar estatus."
            ),
            is_terminal=True,
            order_index=60,
        )
        doubts = BotFlowNode.objects.create(
            flow=flow,
            key="dudas",
            title="Dudas",
            message_text=DOUBTS_MESSAGE,
            is_terminal=True,
            order_index=110,
        )

        for index, row in enumerate(MAIN_MENU_ROWS, start=1):
            action = BotFlowOption.ActionType.GO_TO_MESSAGE
            next_node = booking_categories
            if row["id"] == "Cotizar":
                next_node = quote_categories
            if row["id"] == "Entrega":
                next_node = delivery
            if row["id"] == "Dudas":
                next_node = doubts
            BotFlowOption.objects.create(
                node=start,
                title=row["title"],
                description=row.get("description", ""),
                action_type=action,
                next_node=next_node,
                order_index=index * 10,
            )

        booking_categories_map = {
            "Eventos": events_booking,
            "Sesiones": sessions_booking,
            "Sesiones Tematicas": thematic_booking,
        }
        quote_categories_map = {
            "Eventos": events_quote,
            "Sesiones": sessions_quote,
            "Sesiones Tematicas": thematic_quote,
        }
        for index, row in enumerate(SERVICE_CATEGORY_ROWS, start=1):
            BotFlowOption.objects.create(
                node=booking_categories,
                title=row["title"],
                description=row.get("description", ""),
                action_type=BotFlowOption.ActionType.GO_TO_MESSAGE,
                next_node=booking_categories_map.get(row["id"]),
                order_index=index * 10,
            )
            BotFlowOption.objects.create(
                node=quote_categories,
                title=row["title"],
                description=row.get("description", ""),
                action_type=BotFlowOption.ActionType.GO_TO_MESSAGE,
                next_node=quote_categories_map.get(row["id"]),
                order_index=index * 10,
            )

        for index, row in enumerate(CATEGORY_TO_SERVICES["Eventos"], start=1):
            BotFlowOption.objects.create(
                node=events_booking,
                title=row["title"],
                description=row.get("description", ""),
                action_type=BotFlowOption.ActionType.BOOK_SERVICE,
                service=services.get(row["id"]),
                order_index=index * 10,
            )
            BotFlowOption.objects.create(
                node=events_quote,
                title=row["title"],
                description=row.get("description", ""),
                action_type=BotFlowOption.ActionType.QUOTE_SERVICE,
                service=services.get(row["id"]),
                order_index=index * 10,
            )

        for index, row in enumerate(CATEGORY_TO_SERVICES["Sesiones"], start=1):
            BotFlowOption.objects.create(
                node=sessions_booking,
                title=row["title"],
                description=row.get("description", ""),
                action_type=BotFlowOption.ActionType.BOOK_SERVICE,
                service=services.get(row["id"]),
                order_index=index * 10,
            )
            BotFlowOption.objects.create(
                node=sessions_quote,
                title=row["title"],
                description=row.get("description", ""),
                action_type=BotFlowOption.ActionType.QUOTE_SERVICE,
                service=services.get(row["id"]),
                order_index=index * 10,
            )

        for index, row in enumerate(CATEGORY_TO_SERVICES["Sesiones Tematicas"], start=1):
            BotFlowOption.objects.create(
                node=thematic_booking,
                title=row["title"],
                description=row.get("description", ""),
                action_type=BotFlowOption.ActionType.BOOK_SERVICE,
                service=services.get(row["id"]),
                order_index=index * 10,
            )
            BotFlowOption.objects.create(
                node=thematic_quote,
                title=row["title"],
                description=row.get("description", ""),
                action_type=BotFlowOption.ActionType.QUOTE_SERVICE,
                service=services.get(row["id"]),
                order_index=index * 10,
            )

    return flow


def _find_option(flow: BotFlow, user: User, selected_key: str) -> BotFlowOption | None:
    if user.active_node_id:
        option = (
            BotFlowOption.objects.filter(
                node_id=user.active_node_id,
                is_active=True,
                trigger_key__iexact=selected_key,
            )
            .select_related("node", "next_node", "service")
            .first()
        )
        if option:
            return option

    return (
        BotFlowOption.objects.filter(
            node__flow=flow,
            node__is_active=True,
            is_active=True,
            trigger_key__iexact=selected_key,
        )
        .select_related("node", "next_node", "service")
        .order_by("order_index", "id")
        .first()
    )


def _find_option_by_title(flow: BotFlow, user: User, selected_key: str) -> BotFlowOption | None:
    if user.active_node_id:
        option = (
            BotFlowOption.objects.filter(
                node_id=user.active_node_id,
                is_active=True,
                title__iexact=selected_key,
            )
            .select_related("node", "next_node", "service")
            .first()
        )
        if option:
            return option

    return (
        BotFlowOption.objects.filter(
            node__flow=flow,
            node__is_active=True,
            is_active=True,
            title__iexact=selected_key,
        )
        .select_related("node", "next_node", "service")
        .order_by("order_index", "id")
        .first()
    )


def _go_to_node(sender: str, user: User, flow: BotFlow, node: BotFlowNode | None) -> list[dict]:
    if not node:
        return [text_message(sender, "No hay un siguiente paso configurado.")]
    user.active_flow = flow
    user.active_node = node
    user.save(update_fields=["active_flow", "active_node", "updated_at"])
    return _render_node_payloads(sender, node)


def route_with_flow_nodes(*, sender: str, selected_key: str, user: User, base_url: str) -> list[dict] | None:
    flow = get_active_flow() or ensure_default_bot_flow_seeded()

    if selected_key.lower() in {"hola", "menu", "inicio"}:
        start = get_start_node(flow)
        user.active_flow = flow
        user.active_node = start
        user.conversation_state = User.ConversationState.IDLE
        user.save(update_fields=["active_flow", "active_node", "conversation_state", "updated_at"])
        if not start:
            return None
        return _render_node_payloads(sender, start)

    option = _find_option(flow, user, selected_key) or _find_option_by_title(flow, user, selected_key)
    if option is None:
        return None

    user.active_flow = flow
    user.active_node = option.node
    user.save(update_fields=["active_flow", "active_node", "updated_at"])

    if option.action_type == BotFlowOption.ActionType.GO_TO_START:
        start = get_start_node(flow)
        return _go_to_node(sender, user, flow, start)

    if option.action_type == BotFlowOption.ActionType.OPEN_LINK:
        if option.external_url:
            payloads = [text_message(sender, option.external_url)]
            if option.next_node:
                payloads.extend(_go_to_node(sender, user, flow, option.next_node))
            return payloads
        return [text_message(sender, "Esta opcion no tiene enlace configurado.")]

    if option.action_type == BotFlowOption.ActionType.QUOTE_SERVICE:
        if not option.service:
            return [text_message(sender, "Esta opcion no tiene servicio asignado.")]
        user.conversation_state = User.ConversationState.QUOTE
        user.save(update_fields=["conversation_state", "updated_at"])
        payloads = quote_payload(
            sender,
            option.service.name,
            option.service.quote_url or PIXIESET_DEFAULT_LINK,
        )
        if option.next_node:
            payloads.extend(_go_to_node(sender, user, flow, option.next_node))
        return payloads

    if option.action_type == BotFlowOption.ActionType.BOOK_SERVICE:
        if not option.service:
            return [text_message(sender, "Esta opcion no tiene servicio asignado.")]
        user.conversation_state = User.ConversationState.BOOKING
        user.save(update_fields=["conversation_state", "updated_at"])
        create_booking_intent(user=user, service=option.service, source_option_key=option.trigger_key)
        booking_url = f"{base_url.rstrip('/')}/calendario/{user.booking_token}/"
        payloads = booking_payload(
            sender=sender,
            service_name=option.service.name,
            service_description=option.service.description or "Servicio fotografico.",
            booking_url=booking_url,
        )
        payloads.append(text_message(sender, booking_url))
        return payloads

    if option.action_type == BotFlowOption.ActionType.CLOSE:
        user.conversation_state = User.ConversationState.IDLE
        user.save(update_fields=["conversation_state", "updated_at"])
        return [text_message(sender, "Gracias por escribirnos. Estamos para ayudarte.")]

    target = option.next_node or option.node.default_next
    if target and target.key.lower() == "dudas":
        mark_chat_needs_attention(user)
    elif "duda" in option.title.lower():
        mark_chat_needs_attention(user)
    return _go_to_node(sender, user, flow, target)


def build_mermaid_flow(flow: BotFlow | None) -> str:
    if flow is None:
        return "flowchart TD\n    A[Sin flujo activo]"

    nodes = list(flow.nodes.prefetch_related("options").order_by("order_index", "id"))
    if not nodes:
        return "flowchart TD\n    A[Flujo sin mensajes]"

    lines = ["flowchart TD"]
    for node in nodes:
        node_label = node.title.replace('"', "'")
        lines.append(f'    N{node.id}["{node_label}"]')

    for node in nodes:
        options = node.options.filter(is_active=True).order_by("order_index", "id")
        for option in options:
            label = option.title.replace('"', "'")
            if option.action_type == BotFlowOption.ActionType.BOOK_SERVICE:
                lines.append(f'    N{node.id} -->|"{label}"| BOOK["Accion: Agendar servicio"]')
            elif option.action_type == BotFlowOption.ActionType.QUOTE_SERVICE:
                lines.append(f'    N{node.id} -->|"{label}"| QUOTE["Accion: Cotizar servicio"]')
            elif option.action_type == BotFlowOption.ActionType.OPEN_LINK:
                lines.append(f'    N{node.id} -->|"{label}"| URL["Accion: Enlace"]')
            elif option.next_node_id:
                lines.append(f'    N{node.id} -->|"{label}"| N{option.next_node_id}')
        if node.default_next_id:
            lines.append(f'    N{node.id} -. "Siguiente por defecto" .-> N{node.default_next_id}')

    return "\n".join(lines)
