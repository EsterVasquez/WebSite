from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.models import (
    Booking,
    BookingIntent,
    Message,
    Service,
    ServiceException,
    ServicePackage,
    ServiceWeeklyRange,
    User,
)
from app.services.bot_flow_service import ensure_default_bot_flow_seeded
from app.services.booking_service import create_booking_intent
from app.services.catalog_service import ensure_base_services


def _ensure_temporary_service() -> Service:
    today = timezone.localdate()
    start = today + timedelta(days=7)
    end = today + timedelta(days=75)
    service, _ = Service.objects.get_or_create(
        internal_code="Service_Temporada_2026",
        defaults={
            "name": "Sesión de temporada 2026",
            "slug": "",
            "category": "Sesiones Temáticas",
            "description": "Sesión temporal por temporada con cupo limitado.",
            "quote_url": "",
            "availability_type": Service.AvailabilityType.TEMPORARY,
            "available_from": start,
            "available_until": end,
            "default_duration_minutes": 45,
            "booking_interval_minutes": 15,
            "is_active": True,
        },
    )
    service.availability_type = Service.AvailabilityType.TEMPORARY
    service.available_from = start
    service.available_until = end
    service.default_duration_minutes = 45
    service.booking_interval_minutes = 15
    service.is_active = True
    service.save()

    if not service.weekly_ranges.exists():
        for weekday in range(0, 6):
            ServiceWeeklyRange.objects.create(
                service=service,
                weekday=weekday,
                label="Temporada",
                start_time=time(10, 0),
                end_time=time(14, 0),
                order_index=10,
            )
            ServiceWeeklyRange.objects.create(
                service=service,
                weekday=weekday,
                label="Temporada tarde",
                start_time=time(16, 0),
                end_time=time(20, 0),
                order_index=20,
            )

    if not service.packages.exists():
        ServicePackage.objects.create(
            service=service,
            name="Paquete Temporada Base",
            description="Sesión estándar de temporada.",
            price=900,
            deposit_required=300,
            duration_minutes=45,
            is_default=True,
            is_active=True,
            order_index=10,
        )
        ServicePackage.objects.create(
            service=service,
            name="Paquete Temporada Premium",
            description="Sesión extendida con más fotos editadas.",
            price=1600,
            deposit_required=500,
            duration_minutes=75,
            is_default=False,
            is_active=True,
            order_index=20,
        )
    return service


class Command(BaseCommand):
    help = "Carga datos demo para bot, servicios/eventos, paquetes y citas."

    def handle(self, *args, **options):
        with transaction.atomic():
            BookingIntent.objects.all().delete()
            Booking.objects.all().delete()
            Message.objects.all().delete()
            User.objects.all().delete()
            ServiceException.objects.all().delete()

            ensure_default_bot_flow_seeded()
            services = ensure_base_services()
            temporary_service = _ensure_temporary_service()
            all_services = [*services, temporary_service]

            if all_services:
                next_saturday = timezone.localdate() + timedelta(
                    days=(5 - timezone.localdate().weekday()) % 7
                )
                ServiceException.objects.get_or_create(
                    service=all_services[0],
                    date=next_saturday,
                    exception_type=ServiceException.ExceptionType.MAX_BOOKINGS,
                    defaults={"max_bookings": 2, "notes": "Sábado con cupo limitado", "is_active": True},
                )
                ServiceException.objects.get_or_create(
                    service=all_services[1],
                    date=timezone.localdate() + timedelta(days=10),
                    exception_type=ServiceException.ExceptionType.CLOSED,
                    defaults={"notes": "Bloqueado por producción", "is_active": True},
                )

            demo_users = [
                ("5215511111111", "María González"),
                ("5215522222222", "Carlos Ruiz"),
                ("5215533333333", "Fernanda Hernández"),
                ("5215544444444", "Ana López"),
                ("5215555555555", "Diego Martínez"),
                ("5215566666666", "Laura Jiménez"),
            ]
            users: list[User] = []
            for phone, name in demo_users:
                user = User.objects.create(phone_number=phone, name=name)
                users.append(user)

            for user in users:
                Message.objects.create(
                    user=user,
                    direction=Message.Direction.INCOMING,
                    content="Hola",
                    message_type="text",
                )

            today = timezone.localdate()
            target_dates = [today + timedelta(days=1), today + timedelta(days=2), today + timedelta(days=3)]
            statuses = [Booking.Status.PENDING, Booking.Status.CONFIRMED, Booking.Status.CANCELLED]

            for index, user in enumerate(users):
                service = all_services[index % len(all_services)]
                package = service.packages.filter(is_active=True).order_by("order_index", "id").first()
                duration = package.duration_minutes if package and package.duration_minutes else service.default_duration_minutes
                status = statuses[index % len(statuses)]
                source = Booking.Source.WHATSAPP if index % 2 == 0 else Booking.Source.DASHBOARD
                Booking.objects.create(
                    user=user,
                    service=service,
                    package=package,
                    customer_name=user.name,
                    customer_phone=user.phone_number,
                    customer_notes="Datos de prueba",
                    date=target_dates[index % len(target_dates)],
                    time=time(10 + (index % 5), 0),
                    duration_minutes=duration,
                    total_price=package.price if package else 0,
                    deposit_amount=package.deposit_required if package else 0,
                    status=status,
                    source=source,
                )

            create_booking_intent(user=users[0], service=all_services[0], source_option_key="demo")

            self.stdout.write(self.style.SUCCESS("Datos demo cargados correctamente."))
            self.stdout.write(
                self.style.WARNING(
                    f"URL de prueba (usuario {users[0].phone_number}): /calendario/{users[0].booking_token}/"
                )
            )
