from app.whatsapp.constants import (
    CATEGORY_TO_SERVICES,
    DELIVERY_MESSAGE,
    DOUBTS_MESSAGE,
    MAIN_MENU_ROWS,
    SERVICE_CATEGORY_ROWS,
)


def text_message(to: str, body: str) -> dict:
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }


def interactive_list_message(
    to: str,
    header_text: str,
    body_text: str,
    sections: list[dict],
    button_text: str = "Opciones",
) -> dict:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header_text},
            "body": {"text": body_text},
            "action": {"button": button_text, "sections": sections},
        },
    }


def interactive_cta_url_message(to: str, body_text: str, button_text: str, url: str) -> dict:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "body": {"text": body_text},
            "action": {
                "name": "cta_url",
                "parameters": {
                    "display_text": button_text,
                    "url": url,
                },
            },
        },
    }


def first_message_payloads(sender: str) -> list[dict]:
    sections = [
        {"title": "Agendar", "rows": [MAIN_MENU_ROWS[0]]},
        {"title": "Cotizar", "rows": [MAIN_MENU_ROWS[1]]},
        {"title": "Entrega", "rows": [MAIN_MENU_ROWS[2]]},
        {"title": "Dudas", "rows": [MAIN_MENU_ROWS[3]]},
    ]
    return [
        text_message(
            sender,
            (
                "Hola. Gracias por comunicarte a Jonathan CA Photography.\n"
                "Soy el asistente virtual y te ayudaré con lo que necesites."
            ),
        ),
        interactive_list_message(
            sender,
            "¿Por qué te comunicas con nosotros?",
            "Selecciona una opción para brindarte la mejor atención.",
            sections,
        ),
    ]


def service_categories_payload(sender: str) -> list[dict]:
    sections = [
        {"title": "Servicios", "rows": SERVICE_CATEGORY_ROWS},
    ]
    return [
        interactive_list_message(
            sender,
            "Estos son nuestros servicios",
            "Selecciona una categoría.",
            sections,
        )
    ]


def services_for_category_payload(sender: str, category_id: str) -> list[dict]:
    rows = CATEGORY_TO_SERVICES.get(category_id, [])
    if not rows:
        return [text_message(sender, "No encontré esa categoría. Intenta de nuevo.")]

    sections = [{"title": category_id, "rows": rows}]
    return [
        interactive_list_message(
            sender,
            category_id,
            "Selecciona el servicio que deseas.",
            sections,
        )
    ]


def delivery_payload(sender: str) -> list[dict]:
    return [text_message(sender, DELIVERY_MESSAGE)]


def doubts_payload(sender: str) -> list[dict]:
    return [text_message(sender, DOUBTS_MESSAGE)]


def quote_payload(sender: str, service_name: str, link: str) -> list[dict]:
    return [
        text_message(
            sender,
            (
                f"Servicio: {service_name}\n"
                "Aquí puedes revisar el contenido y precios disponibles:"
            ),
        ),
        text_message(sender, link),
    ]


def booking_payload(sender: str, service_name: str, service_description: str, booking_url: str) -> list[dict]:
    body = (
        f"Servicio seleccionado: {service_name}\n"
        f"{service_description}\n\n"
        "Presiona el botón para abrir tu calendario y elegir fecha y hora."
    )
    return [
        text_message(sender, body),
        interactive_cta_url_message(sender, "Agenda tu cita desde este botón:", "Agendar cita", booking_url),
    ]


def unknown_message_payload(sender: str) -> list[dict]:
    payloads = [text_message(sender, "No entendí tu mensaje. Te comparto el menú principal.")]
    payloads.extend(first_message_payloads(sender))
    return payloads
