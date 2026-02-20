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


def quote_payload(sender: str, service_name: str, link: str) -> list[dict]:
    intro = f"Servicio: {service_name}\nAqui puedes revisar detalles y precios:"
    return [text_message(sender, intro), text_message(sender, link)]


def booking_payload(sender: str, service_name: str, service_description: str, booking_url: str) -> list[dict]:
    body = (
        f"Servicio seleccionado: {service_name}\n"
        f"{service_description}\n\n"
        "Presiona el boton para abrir tu calendario y elegir fecha y hora."
    )
    return [
        text_message(sender, body),
        interactive_cta_url_message(sender, "Agenda tu cita desde este boton:", "Agendar cita", booking_url),
    ]
