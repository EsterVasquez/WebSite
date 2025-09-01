import json
import requests
import os
from dotenv import load_dotenv
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render

load_dotenv()

WHATSAPP_TOKEN = os.environ.get("W_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json"
}


def first_message(sender):

    return [{
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "text",
        "text": {"body": "Hola!!! \nGracias por comunicarte a Jonathan CA Photography. \nSoy el asistente virtual y te ayudaré con todo lo que necesites."}
    },
        {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": sender,
        "type": "interactive",

        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "¿¿Porque te comunicas con nosotros??"
            },
            "body": {
                "text": "Selecciona lo que deseas hacer 👇 para brindarte la mejor atención."
            },
            "action": {
                "button": "Opciones",
                "sections": [
                    {
                        "title": "Agendar",
                        "rows": [
                            {
                                "id": "Agendar",
                                "title": "Agendar",
                                "description": "Agendar: Sesión o Evento ",
                            }
                        ]
                    },
                    {
                        "title": "Cotizar",
                        "rows": [
                            {
                                "id": "Cotizar",
                                "title": "Cotización",
                                "description": "Quiero conocer los precios",
                            }
                        ]
                    },
                    {
                        "title": "Entrega",
                        "rows": [
                            {
                                "id": "Entrega",
                                "title": "Entrega",
                                "description": "Quiero conocer el tiempo de entrega de mis fotos",
                            }
                        ]
                    },
                    {
                        "title": "Dudas",
                        "rows": [
                            {
                                "id": "Dudas",
                                "title": "Dudas/Otro",
                                "description": "Tengo dudas, o las otras opciones no son lo que busco",
                            }
                        ]
                    },
                ]
            }
        }
    }
    ]


def agendar_1(sender):
    return [{
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "text",
        "text": {"body": "Hola!!! \nGracias por comunicarte a Jonathan CA Photography. \nSoy el asistente virtual y te ayudaré a agendar tu sesion de navidad."}
    }]


def cotizar_1(sender):
    return [{
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": sender,
        "type": "interactive",

        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "¿Quieres conocer nuestros precios?"
            },
            "body": {
                "text": "Selecciona 👇 que servicio quieres conocer ."
            },
            "action": {
                "button": "Opciones",
                "sections": [
                    {
                        "title": "Eventos",
                        "rows": [
                            {
                                "id": "Eventos",
                                "title": "Eventos Sociales",
                                "description": "Bodas, XV Años, Graduaciones, Primera Comunion y Bautizos",
                            }
                        ]
                    },
                    {
                        "title": "Sesiones",
                        "rows": [
                            {
                                "id": "Sesiones",
                                "title": "Sesiones de estudio",
                                "description": "Sesione casual, familiar, cumpleaños, maternidad y recien nacido ",
                            }
                        ]
                    },
                    {
                        "title": "Sesiones tematicas ",
                        "rows": [
                            {
                                "id": "Sesiones tematicas",
                                "title": "Sesiones Tematicas",
                                "description": "Sesiones con mamá, sesiones con papá y Sesiones navideñas",
                            }
                        ]
                    },
                ]
            }
        }
    }]


def cotizar_eventos(sender):
    return [{
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": sender,
        "type": "interactive",

        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Eventos"
            },
            "body": {
                "text": "Selecciona 👇 que tipo de evento quieres conocer ."
            },
            "action": {
                "button": "Opciones",
                "sections": [
                    {
                        "title": "Bodas",
                        "rows": [
                            {
                                "id": "Link",
                                "title": "Bodas",
                                "description": " ",
                            }
                        ]
                    },
                    {
                        "title": "Xv Años",
                        "rows": [
                            {
                                "id": "Link",
                                "title": "Xv Años",
                                "description": "",
                            }
                        ]
                    },
                    {
                        "title": "Graduaciones",
                        "rows": [
                            {
                                "id": "Link",
                                "title": "Graduaciones",
                                "description": "",
                            }
                        ]
                    },
                    {
                        "title": "Bautizos o 1ª Comunion",
                        "rows": [
                            {
                                "id": "link",
                                "title": "Buatizos o 1ª Comunión",
                                "description": "",
                            }
                        ]
                    },
                ]
            }
        }
    }
    ]


def cotizar_sesiones(sender):
    return [{
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": sender,
        "type": "interactive",

        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Sesiones de estudio"
            },
            "body": {
                "text": "Selecciona 👇 que tipo de sesion quieres conocer ."
            },
            "action": {
                "button": "Opciones",
                "sections": [
                    {
                        "title": "Casual o familiar",
                        "rows": [
                            {
                                "id": "Link",
                                "title": "Casual o familiar",
                                "description": "Una sesion en el estudio, ya se individual de pareja o familiar.  ",
                            }
                        ]
                    },
                    {
                        "title": "Cumpleaños",
                        "rows": [
                            {
                                "id": "1",
                                "title": "Cumpleaños",
                                "description": "",
                            }
                        ]
                    },
                    {
                        "title": "Maternidad",
                        "rows": [
                            {
                                "id": "2",
                                "title": "Maternidad",
                                "description": "",
                            }
                        ]
                    },
                    {
                        "title": "Recien Nacido",
                        "rows": [
                            {
                                "id": "3",
                                "title": "Recien Nacido",
                                "description": "",
                            }
                        ]
                    },
                ]
            }
        }
    }
    ]


def cotizar_sesiones_tematicas(sender):
    return [{
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": sender,
        "type": "interactive",

        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Eventos"
            },
            "body": {
                "text": "Selecciona 👇 que tipo de evento quieres conocer ."
            },
            "action": {
                "button": "Opciones",
                "sections": [
                    {
                        "title": "Sesión mamá",
                        "rows": [
                            {
                                "id": "link",
                                "title": "Sesión mamá ",
                                "description": " ",
                            }
                        ]
                    },
                    {
                        "title": "Sesión Papá",
                        "rows": [
                            {
                                "id": "link",
                                "title": "Sesión Papá",
                                "description": "",
                            }
                        ]
                    },
                    {
                        "title": "Sesión navideña",
                        "rows": [
                            {
                                "id": "link",
                                "title": "Sesion navideña",
                                "description": "",
                            }
                        ]
                    },
                ]
            }
        }
    }
    ]


def enviar_link(sender):
    # logica de que link enviar segun el servicio que quiere el cliente conocer precios
    return [{
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": sender,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "image",
                "image": {
                    "id": "link_sender"
                }
            },
            "body": {
                "text": "El enlace enviado contiene la informacion. Por favor diganos si desea contratar"
            },
            "footer": {
                "text": "En caso de tener alguna duda, contactenos de nuevo, con gusto rsolveremos sus dudas"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "contratar",
                            "title": "Quiero contratar"
                        }
                    }
                ]
            }
        }
    }]
    
def contratar(sender):
    return[]


def entrega_1(sender):
    return [{
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "text",
        "text": {"body": "Funciona!!!!!"}
    }]


def dudas(sender):

    return [{
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "text",
        "text": {"body": """En un momento una persona del equipo Jonathan CA, se estará comunicando contigo. Si en 48 horas no recibes respuesta por favor marca al numero :\n
                Te recordamos que nuestro horario de atencion es de Lunes a Viernes de 10 am - 2 pm \n 4pm - 8pm"""}
    }]


COMMAND_HANDLERS = {
    "Hola": first_message,
    "Agendar": agendar_1,
    "Cotizar": cotizar_1,
    "Entrega": entrega_1,
    "Dudas": dudas,
    "Eventos": cotizar_eventos,
    "Sesiones": cotizar_sesiones,
    "Sesiones Tematicas": cotizar_sesiones_tematicas,
    "Link": enviar_link,
    "Contratar": contratar

}


def send_messages(payloads):
    """Envía cada payload y maneja errores/respaldos de forma centralizada."""
    for payload in payloads:
        resp = requests.post(URL, headers=HEADERS, json=payload)
        if not resp.ok:
            # podría reintentar, loggear en un sistema de alertas, etc.
            print(f"Error al enviar: {resp.status_code} – {resp.text}")


@csrf_exempt
def webhook(request):

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Mensaje recibido:")
            print(json.dumps(data, indent=2))

            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            messages = value.get("messages")

            if messages:
                message = messages[0]
                print(f"\n{message}\n")
                sender = message["from"]
                type = message["type"]

                if type == "text":

                    text = message["text"]["body"]
                    print(f"Mensaje de {sender}: {text}")
                    handler = COMMAND_HANDLERS.get(text)
                else:
                    id = message["interactive"]["list_reply"]["id"]
                    handler = COMMAND_HANDLERS.get(id)

                if handler:
                    payloads = handler(sender)
                else:
                    payloads = [{
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "text",
                        "text": {"body": "No entiendo tu mensaje."}
                    }]

                send_messages(payloads)

        except Exception as e:
            print(f"Error procesando el mensaje: {e}")

        return HttpResponse("EVENT_RECEIVED", status=200)
    else:
        return HttpResponse("Método no permitido", status=405)


def calendar(request):
    return render(request, "calendar.html")
