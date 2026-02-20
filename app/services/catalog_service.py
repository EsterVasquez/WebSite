from app.models import Service, ServicePackage, ServiceWeeklyRange
from app.whatsapp.constants import PIXIESET_DEFAULT_LINK, SERVICE_DEFINITIONS


def _default_weekly_ranges(service: Service) -> None:
    if service.weekly_ranges.exists():
        return
    for weekday in range(0, 6):
        ServiceWeeklyRange.objects.create(
            service=service,
            weekday=weekday,
            label="Horario matutino",
            start_time="09:00",
            end_time="13:20",
            order_index=10,
        )
        ServiceWeeklyRange.objects.create(
            service=service,
            weekday=weekday,
            label="Horario vespertino",
            start_time="16:00",
            end_time="22:00",
            order_index=20,
        )


def _default_packages(service: Service) -> None:
    if service.packages.exists():
        return

    ServicePackage.objects.create(
        service=service,
        name="Paquete Base",
        description="Incluye la cobertura principal.",
        price=1500,
        deposit_required=500,
        duration_minutes=60,
        is_default=True,
        is_active=True,
        order_index=10,
    )
    ServicePackage.objects.create(
        service=service,
        name="Paquete Completo",
        description="Incluye cobertura extendida y edición adicional.",
        price=3000,
        deposit_required=1000,
        duration_minutes=120,
        is_default=False,
        is_active=True,
        order_index=20,
    )


def ensure_service(internal_code: str) -> Service | None:
    definition = SERVICE_DEFINITIONS.get(internal_code)
    if not definition:
        return None

    service, _ = Service.objects.get_or_create(
        internal_code=internal_code,
        defaults={
            "name": definition["name"],
            "category": definition.get("category", ""),
            "description": definition.get("description", ""),
            "quote_url": PIXIESET_DEFAULT_LINK,
            "availability_type": Service.AvailabilityType.PERMANENT,
            "available_from": None,
            "available_until": None,
            "default_duration_minutes": 60,
            "booking_interval_minutes": 20,
            "is_active": True,
        },
    )
    _default_weekly_ranges(service)
    _default_packages(service)
    return service


def ensure_base_services() -> list[Service]:
    services: list[Service] = []
    for internal_code in SERVICE_DEFINITIONS:
        service = ensure_service(internal_code)
        if service is not None:
            services.append(service)
    return services


def get_service_by_code(internal_code: str) -> Service | None:
    service = Service.objects.filter(internal_code=internal_code, is_active=True).first()
    if service:
        return service
    return ensure_service(internal_code)


def get_service_by_payload(internal_code: str) -> Service | None:
    # Compatibilidad interna para llamadas heredadas.
    return get_service_by_code(internal_code)
