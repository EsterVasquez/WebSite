import json
import requests
import os
import time
import uuid
import logging
from .wa_logs import log_event, log_error, pick_meta, safe_json, logger, request_start, request_end
from dotenv import load_dotenv
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect

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
                                "id": "Sesiones Tematicas",
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
        "Service_XV": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",
        "Service_Graduaciones": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",
        "Service_Bautizo": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",
        "Service_Casual": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",
        "Service_Cumpleaños": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",
        "Service_Maternidad": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",
        "Service_Nacido": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",
        "Service_Mama": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",    
        "Service_Papa": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",
        "Service_Navideña": "https://accounts.pixieset.com/login/?spId=gallery-dashboard",
    }

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
                "text": "En caso de tener alguna duda marcar al 3781088506"
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



def summarize_outgoing(payload: dict) -> str:
    t = payload.get("type")
    to = payload.get("to")

    if t == "text":
        body = (payload.get("text") or {}).get("body", "")
        clean = body.replace("\n", "\\n")
        return f"type=text to={to} len={len(body)} preview='{clean[:120]}'"

    if t == "interactive":
        it = (payload.get("interactive") or {}).get("type")
        header = ((payload.get("interactive") or {}).get("header") or {}).get("text", "")
        return f"type=interactive({it}) to={to} header='{header[:80]}'"

    return f"type={t} to={to}"


# Envia los mensajes y crea los logs
def send_messages(payloads, request_id: str):
    for i, payload in enumerate(payloads, start=1):
        log_event("OUTGOING_SEND", request_id, n=f"{i}/{len(payloads)}", summary=summarize_outgoing(payload))
        payload_logger = logging.getLogger("wa_payloads")
        payload_logger.debug(f"OUTGOING_PAYLOAD | request_id={request_id}\n{safe_json(payload, max_len=20000)}")
        t0 = time.time()
        try:
            resp = requests.post(URL, headers=HEADERS, json=payload, timeout=15)
            ms = int((time.time() - t0) * 1000)

            if resp.ok:
                log_event("OUTGOING_OK", request_id, status=resp.status_code, ms=ms)
            else:
                log_error("OUTGOING_FAIL", request_id, status=resp.status_code, ms=ms, resp=resp.text[:500].replace("\n", " "))
        except requests.RequestException as e:
            log_error("OUTGOING_EXCEPTION", request_id, err=str(e))


@csrf_exempt
def webhook(request):
    t0 = time.perf_counter()
    request_id = uuid.uuid4().hex[:10]
    payloads = []

    if request.method != "POST":
        log_event("WEBHOOK_METHOD_NOT_ALLOWED", request_id, method=request.method)
        return HttpResponse("Método no permitido", status=405)

    try:
        data = json.loads(request.body)

        entry = (data.get("entry") or [{}])[0]
        changes = (entry.get("changes") or [{}])[0]
        value = changes.get("value") or {}

        #Si NO hay messages => ignorar COMPLETAMENTE (statuses, delivery, read, etc.)
        messages = value.get("messages")
        if not messages:
            return HttpResponse("EVENT_RECEIVED", status=200)

        meta = pick_meta(data)
        request_start(request_id, **meta)
        log_event("INCOMING", request_id, **meta)

        message = messages[0]
        sender = message["from"]
        message_type = message["type"]

        handler = None
        selected_key = None

        if message_type == "text":
            selected_key = message["text"]["body"]
            handler = COMMAND_HANDLERS.get(selected_key)
        else:
            interactive = message.get("interactive") or {}
            list_reply = interactive.get("list_reply")
            button_reply = interactive.get("button_reply")

            if list_reply:
                selected_key = list_reply.get("id")
            elif button_reply:
                selected_key = button_reply.get("id")

            if selected_key and "_" in selected_key:
                payloads = agendar_o_cotizar_serivicio(selected_key, sender)
                log_event("ROUTE_SPECIAL", request_id, key=selected_key)
            else:
                handler = COMMAND_HANDLERS.get(selected_key)

        log_event("ROUTE", request_id, key=selected_key, has_handler=bool(handler), payloads_pre=len(payloads))

        if not payloads and handler:
            payloads = handler(sender)

        if not payloads:
            payloads = [{
                "messaging_product": "whatsapp",
                "to": sender,
                "type": "text",
                "text": {"body": "No entiendo tu mensaje."}
            }]

        log_event("PAYLOADS_READY", request_id, count=len(payloads), to=sender)

        send_messages(payloads, request_id=request_id)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        request_end(request_id, ms=elapsed_ms, sent=len(payloads))

    except Exception as e:
        # log con contexto
        log_error("WEBHOOK_EXCEPTION", request_id, err=str(e))
        # si quieres, también guarda el body recortado (útil para debug)
        try:
            raw = request.body.decode("utf-8", errors="ignore")
            log_error("RAW_BODY", request_id, body=raw[:2000])
        except Exception:
            pass

    return HttpResponse("EVENT_RECEIVED", status=200)


def calendar(request):
    return render(request, "calendar.html")


def user_calendar(request):
    return render(request, "user_calendar.html")

def auth_login(request):
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