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

options_cotizar_agendar = " "

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
                                "description": "",
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


def create_services_payload(sender):

    return [{
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": sender,
        "type": "interactive",

        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Esto son nuestros servicios 😃"
            },
            "body": {
                "text": "Selecciona 👇."
            },
            "action": {
                "button": "Opciones",
                "sections": [
                    {
                        "title": "Eventos",
                        "rows": [
                            {
                                "id": "Eventos",
                                "title": "Eventos Sociales:",
                                "description": "Bodas, XV Años, Graduaciones, Primera Comunion y Bautizos",
                            }
                        ]
                    },
                    {
                        "title": "Sesiones",
                        "rows": [
                            {
                                "id": "Sesiones",
                                "title": "Sesiones de estudio:",
                                "description": "Sesione casual, familiar, cumpleaños, maternidad y recien nacido ",
                            }
                        ]
                    },
                    {
                        "title": "Sesiones tematicas ",
                        "rows": [
                            {
                                "id": "Sesiones tematicas",
                                "title": "Sesiones Tematicas:",
                                "description": "Sesiones con mamá, sesiones con papá y Sesiones navideñas",
                            }
                        ]
                    },
                ]
            }
        }
    }]


def cotizar_1(sender):
    global options_cotizar_agendar
    options_cotizar_agendar = "cotizar"
    servicios = create_services_payload(sender)
    print(servicios)
    return servicios


def agendar_1(sender):
    global options_cotizar_agendar
    options_cotizar_agendar = "agendar"
    servicios = create_services_payload(sender)
    return servicios


def eventos(sender):
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
                "text": "Selecciona 👇 que tipo de evento."
            },
            "action": {
                "button": "Opciones",
                "sections": [
                    {
                        "title": "Bodas",
                        "rows": [
                            {
                                "id": "Service_Boda",
                                "title": "Bodas",
                                "description": " ",
                            }
                        ]
                    },
                    {
                        "title": "Xv Años",
                        "rows": [
                            {
                                "id": "Service_XV",
                                "title": "Xv Años",
                                "description": "",
                            }
                        ]
                    },
                    {
                        "title": "Graduaciones",
                        "rows": [
                            {
                                "id": "Service_Graduaciones",
                                "title": "Graduaciones",
                                "description": "",
                            }
                        ]
                    },
                    {
                        "title": "Bautizos o 1ª Comunion",
                        "rows": [
                            {
                                "id": "Service_Bautizo",
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


def sesiones(sender):
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
                "text": "Sesiones para cada ocasión 🤩."
            },
            "action": {
                "button": "Opciones",
                "sections": [
                    {
                        "title": "Casual o familiar",
                        "rows": [
                            {
                                "id": "Service_Casual",
                                "title": "Casual o familiar",
                                "description": "Puede ser individual, de pareja o familiar.",
                            }
                        ]
                    },
                    {
                        "title": "Cumpleaños",
                        "rows": [
                            {
                                "id": "Service_Cumpleaños",
                                "title": "Cumpleaños",
                                "description": "",
                            }
                        ]
                    },
                    {
                        "title": "Maternidad",
                        "rows": [
                            {
                                "id": "Service_Maternidad",
                                "title": "Maternidad",
                                "description": "",
                            }
                        ]
                    },
                    {
                        "title": "Recien Nacido",
                        "rows": [
                            {
                                "id": "Service_Nacido",
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


def sesiones_tematicas(sender):
    return [{
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": sender,
        "type": "interactive",

        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Sesiones temáticas"
            },
            "body": {
                "text": "Nuestras sesiones para las épocas especiales del año "
            },
            "action": {
                "button": "Opciones",
                "sections": [
                    {
                        "title": "Dia de las madres",
                        "rows": [
                            {
                                "id": "Service_Mama",
                                "title": "Dia de las madres ",
                                "description": " ",
                            }
                        ]
                    },
                    {
                        "title": "Día del padre",
                        "rows": [
                            {
                                "id": "Service_Papa",
                                "title": "Dia del padre",
                                "description": "",
                            }
                        ]
                    },
                    {
                        "title": "Sesión navideña",
                        "rows": [
                            {
                                "id": "Service_Navideña",
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

    # logica de que link enviar segun el servicio que quiere el cliente conocer precios
    return []


def contratar(sender):
    return []


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
    "Eventos": eventos,
    "Sesiones": sesiones,
    "Sesiones Tematicas": sesiones_tematicas,

}

# funciones que no se usan en el diccionario


def agendar_o_cotizar_serivicio(id, sender):
    LINKS = {
        "Service_Boda": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",
    }
    partes = id.split("_")

    # podria usar un interactive call to action button
    return [{
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "text",
        "text": {"body": LINKS[id]}
            },
        {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": sender,
        "type": "interactive",
        "interactive": {
            "type": "button",
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
    }
            ]


def send_messages(payloads):
    """Envía cada payload y maneja errores/respaldos de forma centralizada."""
    for payload in payloads:
        resp = requests.post(URL, headers=HEADERS, json=payload)
        if not resp.ok:
            # podría reintentar, loggear en un sistema de alertas, etc.
            print(f"Error al enviar: {resp.status_code} – {resp.text}")


@csrf_exempt
def webhook(request):
    payloads =[]

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
                message_type = message["type"]

                if message_type == "text":
                    text = message["text"]["body"]
                    handler = COMMAND_HANDLERS.get(text)

                else:
                    id = message["interactive"]["list_reply"]["id"]
                    if "_" in id:
                        payloads = agendar_o_cotizar_serivicio(id, sender)
                    else:
                        handler = COMMAND_HANDLERS.get(id)


                if payloads:
                    pass
                elif handler:
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


def user_calendar(request):
    return render(request, "user_calendar.html")

def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("calendar")  # o la vista principal
        else:
            return render(
                request,
                "login.html",
                {"error": "Usuario o contraseña incorrectos"},
            )

    # GET
    return render(request, "login.html")