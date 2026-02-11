from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.models import Booking, BookingIntent, Message, TimeBlock, User
from app.services.booking_service import create_booking_intent
from app.services.catalog_service import WEEKDAYS, ensure_service, ensure_weekdays
from app.whatsapp.constants import SERVICE_DEFINITIONS


class Command(BaseCommand):
    help = "Carga datos de prueba realistas para flujo completo WhatsApp -> web -> reservación."

    def handle(self, *args, **options):
        with transaction.atomic():
            days = ensure_weekdays()
            services = [ensure_service(payload_id) for payload_id in SERVICE_DEFINITIONS]

            day_by_name = {day.day: day for day in days}
            working_days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
            for service in services:
                if service is None:
                    continue

                for day_name in working_days:
                    day = day_by_name[day_name]
                    TimeBlock.objects.get_or_create(
                        service=service,
                        day=day,
                        name="Matutino",
                        defaults={"start_time": time(10, 0), "end_time": time(14, 0)},
                    )
                    TimeBlock.objects.get_or_create(
                        service=service,
                        day=day,
                        name="Vespertino",
                        defaults={"start_time": time(15, 0), "end_time": time(20, 0)},
                    )

            demo_users = [
                ("5215511111111", "María González"),
                ("5215522222222", "Carlos Ruiz"),
                ("5215533333333", "Fernanda Hernández"),
                ("5215544444444", "Ana López"),
            ]
            users = []
            for phone, name in demo_users:
                user, _ = User.objects.get_or_create(phone_number=phone, defaults={"name": name})
                if user.name != name:
                    user.name = name
                    user.save(update_fields=["name", "updated_at"])
                users.append(user)

            for user in users:
                Message.objects.get_or_create(
                    user=user,
                    direction=Message.Direction.INCOMING,
                    content="Hola",
                    message_type="text",
                )

            today = timezone.localdate()
            target_dates = [today + timedelta(days=1), today + timedelta(days=2), today + timedelta(days=3)]

            all_tiers = []
            for service in services:
                if service:
                    all_tiers.extend(list(service.tiers.order_by("price")))

            for index, user in enumerate(users):
                tier = all_tiers[index % len(all_tiers)]
                Booking.objects.get_or_create(
                    user=user,
                    service_tier=tier,
                    date=target_dates[index % len(target_dates)],
                    time=time(10 + index, 0),
                    defaults={
                        "status": "Pendiente" if index % 2 == 0 else "Confirmado",
                        "source": "whatsapp",
                    },
                )

            # Mantener una intención abierta para probar user_calendar.
            intent_user = users[0]
            open_service = services[0]
            if open_service:
                create_booking_intent(intent_user, open_service, open_service.payload_id)

            self.stdout.write(self.style.SUCCESS("Datos demo cargados correctamente."))
            self.stdout.write(
                self.style.WARNING(
                    f"URL de prueba (usuario {intent_user.phone_number}): /calendario/{intent_user.booking_token}/"
                )
            )
