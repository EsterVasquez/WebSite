PIXIESET_DEFAULT_LINK = "https://accounts.pixieset.com/login/?spId=gallery-dashboard"

MAIN_MENU_ROWS = [
    {"id": "Agendar", "title": "Agendar", "description": "Agenda tu cita con nosotros"},
    {"id": "Cotizar", "title": "Cotización", "description": "Quiero conocer los precios"},
    {
        "id": "Entrega",
        "title": "Entrega",
        "description": "Quiero conocer el tiempo de entrega de mis fotos",
    },
    {
        "id": "Dudas",
        "title": "Dudas/Otro",
        "description": "Tengo dudas o las otras opciones no son lo que busco",
    },
]

SERVICE_CATEGORY_ROWS = [
    {
        "id": "Eventos",
        "title": "Eventos Sociales",
        "description": "Bodas, XV Años, Graduaciones, Primera Comunión y Bautizos",
    },
    {
        "id": "Sesiones",
        "title": "Sesiones de estudio",
        "description": "Casual, familiar, cumpleaños, maternidad y recién nacido",
    },
    {
        "id": "Sesiones Tematicas",
        "title": "Sesiones Temáticas",
        "description": "Sesiones con mamá, sesiones con papá y sesiones navideñas",
    },
]

CATEGORY_TO_SERVICES = {
    "Eventos": [
        {"id": "Service_Boda", "title": "Bodas", "description": ""},
        {"id": "Service_XV", "title": "XV Años", "description": ""},
        {"id": "Service_Graduaciones", "title": "Graduaciones", "description": ""},
        {"id": "Service_Bautizo", "title": "Bautizos o 1ª Comunión", "description": ""},
    ],
    "Sesiones": [
        {
            "id": "Service_Casual",
            "title": "Casual o familiar",
            "description": "Puede ser individual, de pareja o familiar",
        },
        {"id": "Service_Cumpleaños", "title": "Cumpleaños", "description": ""},
        {"id": "Service_Maternidad", "title": "Maternidad", "description": ""},
        {"id": "Service_Nacido", "title": "Recién nacido", "description": ""},
    ],
    "Sesiones Tematicas": [
        {"id": "Service_Mama", "title": "Día de las madres", "description": ""},
        {"id": "Service_Papa", "title": "Día del padre", "description": ""},
        {"id": "Service_Navideña", "title": "Sesión navideña", "description": ""},
    ],
}

SERVICE_DEFINITIONS = {
    "Service_Boda": {
        "name": "Bodas",
        "category": "Eventos",
        "description": "Cobertura completa para boda civil o religiosa.",
    },
    "Service_XV": {
        "name": "XV Años",
        "category": "Eventos",
        "description": "Cobertura de misa, sesión y recepción.",
    },
    "Service_Graduaciones": {
        "name": "Graduaciones",
        "category": "Eventos",
        "description": "Cobertura en estudio o locación para graduación.",
    },
    "Service_Bautizo": {
        "name": "Bautizos o 1ª Comunión",
        "category": "Eventos",
        "description": "Cobertura de ceremonia y convivencia.",
    },
    "Service_Casual": {
        "name": "Casual o familiar",
        "category": "Sesiones",
        "description": "Sesión individual, en pareja o familiar.",
    },
    "Service_Cumpleaños": {
        "name": "Cumpleaños",
        "category": "Sesiones",
        "description": "Sesión temática de cumpleaños en estudio.",
    },
    "Service_Maternidad": {
        "name": "Maternidad",
        "category": "Sesiones",
        "description": "Sesión de maternidad en estudio o exterior.",
    },
    "Service_Nacido": {
        "name": "Recién nacido",
        "category": "Sesiones",
        "description": "Sesión newborn con set especializado.",
    },
    "Service_Mama": {
        "name": "Día de las madres",
        "category": "Sesiones Tematicas",
        "description": "Sesión especial por temporada del Día de las Madres.",
    },
    "Service_Papa": {
        "name": "Día del padre",
        "category": "Sesiones Tematicas",
        "description": "Sesión especial por temporada del Día del Padre.",
    },
    "Service_Navideña": {
        "name": "Sesión navideña",
        "category": "Sesiones Tematicas",
        "description": "Sesión navideña en set temático.",
    },
}

DELIVERY_MESSAGE = (
    "Nuestro tiempo de entrega depende del servicio. "
    "Si ya tienes una reserva, comparte tu nombre para revisar el estatus."
)

DOUBTS_MESSAGE = (
    "En un momento una persona del equipo Jonathan CA se comunicará contigo. "
    "Horario de atención: lunes a viernes, 10:00 a 14:00 y 15:00 a 20:00."
)
