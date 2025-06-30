import json
import requests
import os
from dotenv import load_dotenv
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

load_dotenv()

WHATSAPP_TOKEN = os.environ.get("W_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")


def handle_opcion_1(sender):
    return {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "text",
        "text": {"body": "Elegiste Opción 1"}
    }


def handle_opcion_2(sender):
    return {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "text",
        "text": {"body": "Elegiste Opción 2"}
    }


COMMAND_HANDLERS = {
    "Opcion 1": handle_opcion_1,
    "Opcion 2": handle_opcion_2,
}


@csrf_exempt
def webhook(request):
    URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    HEADERS = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

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
                    payload = handler(sender)
                else:
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "text",
                        "text": {"body": "No entiendo tu mensaje."}
                    }

                response = requests.post(URL, headers=HEADERS, json=payload)
                print(
                    f"Respuesta enviada: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Error procesando el mensaje: {e}")

        return HttpResponse("EVENT_RECEIVED", status=200)
    else:
        return HttpResponse("Método no permitido", status=405)
