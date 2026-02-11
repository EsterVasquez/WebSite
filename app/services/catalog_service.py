from datetime import timedelta

from django.utils import timezone

from app.models import Day, Service, ServiceTier
from app.whatsapp.constants import PIXIESET_DEFAULT_LINK, SERVICE_DEFINITIONS


WEEKDAYS = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


def ensure_weekdays() -> list[Day]:
    days = []
    for name in WEEKDAYS:
        day, _ = Day.objects.get_or_create(day=name)
        days.append(day)
    return days


def ensure_service(payload_id: str) -> Service | None:
    definition = SERVICE_DEFINITIONS.get(payload_id)
    if not definition:
        return None

    today = timezone.localdate()
    service, _ = Service.objects.get_or_create(
        payload_id=payload_id,
        defaults={
            "name": definition["name"],
            "category": definition["category"],
            "description": definition["description"],
            "link": PIXIESET_DEFAULT_LINK,
            "available_from": today,
            "available_until": today + timedelta(days=365),
            "is_active": True,
        },
    )

    if not service.days.exists():
        service.days.set(ensure_weekdays())

    if not service.tiers.exists():
        ServiceTier.objects.create(
            service=service,
            name="Paquete Base",
            price=1500,
            duration_minutes=60,
            is_default=True,
        )
        ServiceTier.objects.create(
            service=service,
            name="Paquete Completo",
            price=3000,
            duration_minutes=120,
            is_default=False,
        )
    return service


def get_service_by_payload(payload_id: str) -> Service | None:
    service = Service.objects.filter(payload_id=payload_id, is_active=True).first()
    if service:
        return service
    return ensure_service(payload_id)
