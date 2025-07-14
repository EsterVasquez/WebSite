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

def handle_opcion_1(sender):

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
                                "description": "Quiero conocer el tiempo de entrega de mi material",
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


# def handle_opcion_2(sender):
#     return {
#         "messaging_product": "whatsapp",
#         "to": sender,
#         "type": "text",
#         "text": {"body": "Hola!!! \nGracias por comunicarte con Jonathan CA Photogrphy. \nSoy el asistente virtual que estara resolviendo tus dudas"}
#     }


COMMAND_HANDLERS = {
    "Hola": handle_opcion_1,
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
                sender = message["from"]
                text = message["text"]["body"]
                print(f"Mensaje de {sender}: {text}")

                handler = COMMAND_HANDLERS.get(text)
                if handler:
                    payloads = handler(sender)
                else:
                    payloads = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "text",
                        "text": {"body": "No entiendo tu mensaje."}
                    }

                send_messages(payloads)
                response = requests.post(URL, headers=HEADERS, json=payloads)
                print(
                    f"Respuesta enviada: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Error procesando el mensaje: {e}")

        return HttpResponse("EVENT_RECEIVED", status=200)
    else:
        return HttpResponse("Método no permitido", status=405)


def calendar(request):
    return render(request, "calendar.html")
