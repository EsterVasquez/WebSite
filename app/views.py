import json
import requests
import os
from dotenv import load_dotenv
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

load_dotenv()

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

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

                # Enviar respuesta "hola"
                url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": sender,
                    "type": "text",
                    "text": {"body": "hola"}
                }
                response = requests.post(url, headers=headers, json=payload)
                print(
                    f"Respuesta enviada: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Error procesando el mensaje: {e}")

        return HttpResponse("EVENT_RECEIVED", status=200)
    else:
        return HttpResponse("Método no permitido", status=405)