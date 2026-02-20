import json
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from app.models import BotFlow, BotFlowNode, BotFlowOption, Service
from app.services.bot_flow_service import build_mermaid_flow, ensure_default_bot_flow_seeded


def _active_flow() -> BotFlow:
    flow = (
        BotFlow.objects.filter(is_active=True, is_published=True)
        .order_by("-updated_at", "id")
        .first()
    )
    return flow or ensure_default_bot_flow_seeded()


def _next_order(queryset) -> int:
    max_order = queryset.aggregate(v=Max("order_index")).get("v") or 0
    return max_order + 10


def _is_checked(value: str | None) -> bool:
    return value in {"on", "true", "1", "yes"}


def _generate_node_key(flow: BotFlow) -> str:
    while True:
        candidate = f"node_{uuid.uuid4().hex[:10]}"
        if not flow.nodes.filter(key=candidate).exists():
            return candidate


def _flow_context(selected_node_id: int | None = None) -> dict:
    flow = _active_flow()
    nodes = list(flow.nodes.prefetch_related("options").order_by("order_index", "id"))
    selected_node = None
    if selected_node_id:
        selected_node = next((item for item in nodes if item.id == selected_node_id), None)
    if selected_node is None and nodes:
        selected_node = next((item for item in nodes if item.is_start), None) or nodes[0]

    selected_options = list(selected_node.options.order_by("order_index", "id")) if selected_node else []
    return {
        "flow": flow,
        "nodes": nodes,
        "selected_node": selected_node,
        "selected_options": selected_options,
        "services": Service.objects.filter(is_active=True).order_by("name"),
        "interaction_choices": BotFlowNode.InteractionType.choices,
        "option_action_choices": BotFlowOption.ActionType.choices,
        "mermaid_code": build_mermaid_flow(flow),
    }


def _sanitize_node_by_interaction(node: BotFlowNode) -> None:
    if node.interaction_type == BotFlowNode.InteractionType.TEXT_ONLY:
        node.menu_title = ""
        node.menu_description = ""
        node.menu_button_text = "Ver opciones"
        node.link_button_text = ""
        node.link_button_url = ""
    elif node.interaction_type == BotFlowNode.InteractionType.OPTION_LIST:
        node.link_button_text = ""
        node.link_button_url = ""
        node.menu_button_text = node.menu_button_text or "Ver opciones"
    elif node.interaction_type == BotFlowNode.InteractionType.URL_BUTTON:
        node.menu_title = ""
        node.menu_button_text = "Ver opciones"


def _validate_node_configuration(*, interaction_type: str, link_button_text: str, link_button_url: str) -> str | None:
    if interaction_type == BotFlowNode.InteractionType.URL_BUTTON:
        if not link_button_text.strip():
            return "El tipo 'Botón con enlace' requiere texto para el botón."
        if not link_button_url.strip():
            return "El tipo 'Botón con enlace' requiere una URL."
    return None


def _validate_option_configuration(
    *,
    action_type: str,
    next_node_id: str | None,
    service_id: str | None,
    external_url: str | None,
) -> str | None:
    if action_type == BotFlowOption.ActionType.GO_TO_MESSAGE and not next_node_id:
        return "La acción 'Ir a otro mensaje' requiere elegir un mensaje destino."
    if action_type in {BotFlowOption.ActionType.QUOTE_SERVICE, BotFlowOption.ActionType.BOOK_SERVICE} and not service_id:
        return "La acción seleccionada requiere un servicio."
    if action_type == BotFlowOption.ActionType.OPEN_LINK and not (external_url or "").strip():
        return "La acción 'Enviar enlace' requiere una URL."
    return None


def _sanitize_option_by_action(option: BotFlowOption) -> None:
    if option.action_type == BotFlowOption.ActionType.GO_TO_MESSAGE:
        option.service = None
        option.external_url = ""
    elif option.action_type in {BotFlowOption.ActionType.QUOTE_SERVICE, BotFlowOption.ActionType.BOOK_SERVICE}:
        option.external_url = ""
    elif option.action_type == BotFlowOption.ActionType.OPEN_LINK:
        option.service = None
    elif option.action_type in {BotFlowOption.ActionType.GO_TO_START, BotFlowOption.ActionType.CLOSE}:
        option.next_node = None
        option.service = None
        option.external_url = ""


@login_required
def bot_manager(request):
    selected_node_id = request.GET.get("node")
    context = _flow_context(int(selected_node_id)) if selected_node_id and selected_node_id.isdigit() else _flow_context()
    return render(request, "bot_manager.html", context)


@login_required
@require_POST
def create_node(request):
    flow = _active_flow()
    title = (request.POST.get("title") or "").strip()
    if not title:
        messages.error(request, "Debes indicar el nombre del mensaje.")
        return redirect("bot_manager")

    interaction_type = request.POST.get("interaction_type") or BotFlowNode.InteractionType.TEXT_ONLY
    link_button_text = (request.POST.get("link_button_text") or "").strip()
    link_button_url = (request.POST.get("link_button_url") or "").strip()
    validation_error = _validate_node_configuration(
        interaction_type=interaction_type,
        link_button_text=link_button_text,
        link_button_url=link_button_url,
    )
    if validation_error:
        messages.error(request, validation_error)
        return redirect("bot_manager")

    node = BotFlowNode.objects.create(
        flow=flow,
        key=_generate_node_key(flow),
        title=title,
        message_text=(request.POST.get("message_text") or "").strip(),
        interaction_type=interaction_type,
        menu_title=(request.POST.get("menu_title") or "").strip(),
        menu_description=(request.POST.get("menu_description") or "").strip(),
        menu_button_text=(request.POST.get("menu_button_text") or "Ver opciones").strip() or "Ver opciones",
        link_button_text=link_button_text,
        link_button_url=link_button_url,
        is_terminal=_is_checked(request.POST.get("is_terminal")),
        is_active=True,
        order_index=_next_order(flow.nodes),
    )
    _sanitize_node_by_interaction(node)
    node.save(
        update_fields=[
            "menu_title",
            "menu_description",
            "menu_button_text",
            "link_button_text",
            "link_button_url",
            "updated_at",
        ]
    )
    if request.POST.get("set_as_start"):
        BotFlowNode.objects.filter(flow=flow, is_start=True).exclude(id=node.id).update(is_start=False)
        node.is_start = True
        node.save(update_fields=["is_start", "updated_at"])

    messages.success(request, f"Mensaje '{node.title}' creado.")
    return redirect(f"/bot-manager/?node={node.id}")


@login_required
@require_POST
def update_node(request, node_id: int):
    node = get_object_or_404(BotFlowNode, id=node_id)
    interaction_type = request.POST.get("interaction_type") or BotFlowNode.InteractionType.TEXT_ONLY
    link_button_text = (request.POST.get("link_button_text") or "").strip()
    link_button_url = (request.POST.get("link_button_url") or "").strip()
    validation_error = _validate_node_configuration(
        interaction_type=interaction_type,
        link_button_text=link_button_text,
        link_button_url=link_button_url,
    )
    if validation_error:
        messages.error(request, validation_error)
        return redirect(f"/bot-manager/?node={node.id}")

    node.title = (request.POST.get("title") or node.title).strip() or node.title
    node.message_text = (request.POST.get("message_text") or "").strip()
    node.interaction_type = interaction_type
    node.menu_title = (request.POST.get("menu_title") or "").strip()
    node.menu_description = (request.POST.get("menu_description") or "").strip()
    node.menu_button_text = (request.POST.get("menu_button_text") or "Ver opciones").strip() or "Ver opciones"
    node.link_button_text = link_button_text
    node.link_button_url = link_button_url
    node.is_terminal = _is_checked(request.POST.get("is_terminal"))
    node.is_active = _is_checked(request.POST.get("is_active"))

    default_next_id = request.POST.get("default_next_id")
    node.default_next = BotFlowNode.objects.filter(flow=node.flow, id=default_next_id).first() if default_next_id else None
    _sanitize_node_by_interaction(node)
    node.save(
        update_fields=[
            "title",
            "message_text",
            "interaction_type",
            "menu_title",
            "menu_description",
            "menu_button_text",
            "link_button_text",
            "link_button_url",
            "is_terminal",
            "is_active",
            "default_next",
            "updated_at",
        ]
    )

    if request.POST.get("set_as_start"):
        BotFlowNode.objects.filter(flow=node.flow, is_start=True).exclude(id=node.id).update(is_start=False)
        node.is_start = True
        node.save(update_fields=["is_start", "updated_at"])

    messages.success(request, "Mensaje actualizado.")
    return redirect(f"/bot-manager/?node={node.id}")


@login_required
@require_POST
def delete_node(request, node_id: int):
    node = get_object_or_404(BotFlowNode, id=node_id)
    flow_id = node.flow_id
    was_start = node.is_start
    node.delete()

    if was_start:
        replacement = BotFlowNode.objects.filter(flow_id=flow_id).order_by("order_index", "id").first()
        if replacement:
            replacement.is_start = True
            replacement.save(update_fields=["is_start", "updated_at"])

    messages.success(request, "Mensaje eliminado.")
    return redirect("bot_manager")


@login_required
@require_POST
def create_option(request, node_id: int):
    node = get_object_or_404(BotFlowNode, id=node_id)
    title = (request.POST.get("title") or "").strip()
    if not title:
        messages.error(request, "La opción necesita un título.")
        return redirect(f"/bot-manager/?node={node.id}")

    action_type = request.POST.get("action_type") or BotFlowOption.ActionType.GO_TO_MESSAGE
    next_node_id = request.POST.get("next_node_id")
    service_id = request.POST.get("service_id")
    external_url = (request.POST.get("external_url") or "").strip()
    validation_error = _validate_option_configuration(
        action_type=action_type,
        next_node_id=next_node_id,
        service_id=service_id,
        external_url=external_url,
    )
    if validation_error:
        messages.error(request, validation_error)
        return redirect(f"/bot-manager/?node={node.id}")

    option = BotFlowOption.objects.create(
        node=node,
        title=title,
        description=(request.POST.get("description") or "").strip(),
        action_type=action_type,
        next_node=BotFlowNode.objects.filter(flow=node.flow, id=next_node_id).first() if next_node_id else None,
        service=Service.objects.filter(id=service_id, is_active=True).first() if service_id else None,
        external_url=external_url,
        is_active=True,
        order_index=_next_order(node.options),
    )
    _sanitize_option_by_action(option)
    option.save(update_fields=["next_node", "service", "external_url", "updated_at"])
    messages.success(request, f"Opción '{option.title}' creada.")
    return redirect(f"/bot-manager/?node={node.id}")


@login_required
@require_POST
def update_option(request, option_id: int):
    option = get_object_or_404(BotFlowOption, id=option_id)
    option.title = (request.POST.get("title") or option.title).strip() or option.title
    option.description = (request.POST.get("description") or "").strip()
    option.action_type = request.POST.get("action_type") or BotFlowOption.ActionType.GO_TO_MESSAGE
    option.is_active = _is_checked(request.POST.get("is_active"))

    next_node_id = request.POST.get("next_node_id")
    service_id = request.POST.get("service_id")
    external_url = (request.POST.get("external_url") or "").strip()
    validation_error = _validate_option_configuration(
        action_type=option.action_type,
        next_node_id=next_node_id,
        service_id=service_id,
        external_url=external_url,
    )
    if validation_error:
        messages.error(request, validation_error)
        return redirect(f"/bot-manager/?node={option.node_id}")

    option.next_node = BotFlowNode.objects.filter(flow=option.node.flow, id=next_node_id).first() if next_node_id else None

    option.service = Service.objects.filter(id=service_id, is_active=True).first() if service_id else None
    option.external_url = external_url
    _sanitize_option_by_action(option)
    option.save(
        update_fields=[
            "title",
            "description",
            "action_type",
            "next_node",
            "service",
            "external_url",
            "is_active",
            "updated_at",
        ]
    )
    messages.success(request, "Opción actualizada.")
    return redirect(f"/bot-manager/?node={option.node_id}")


@login_required
@require_POST
def delete_option(request, option_id: int):
    option = get_object_or_404(BotFlowOption, id=option_id)
    node_id = option.node_id
    option.delete()
    messages.success(request, "Opción eliminada.")
    return redirect(f"/bot-manager/?node={node_id}")


def _reorder(items: list, ids: list[int], field_name: str = "order_index") -> None:
    order_map = {item_id: index for index, item_id in enumerate(ids, start=1)}
    for item in items:
        new_order = order_map.get(item.id)
        if new_order is None:
            continue
        setattr(item, field_name, new_order * 10)
    if items:
        type(items[0]).objects.bulk_update(items, [field_name, "updated_at"])


@login_required
@require_POST
def reorder_nodes(request):
    payload = json.loads(request.body or "{}")
    ids = [int(item) for item in (payload.get("ids") or []) if str(item).isdigit()]
    flow = _active_flow()
    items = list(BotFlowNode.objects.filter(flow=flow, id__in=ids))
    _reorder(items, ids)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def reorder_options(request, node_id: int):
    payload = json.loads(request.body or "{}")
    ids = [int(item) for item in (payload.get("ids") or []) if str(item).isdigit()]
    items = list(BotFlowOption.objects.filter(node_id=node_id, id__in=ids))
    _reorder(items, ids)
    return JsonResponse({"ok": True})
