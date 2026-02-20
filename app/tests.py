from datetime import time, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from app.models import Booking, Service, ServicePackage, ServiceWeeklyRange, User
from app.services.bot_flow_service import ensure_default_bot_flow_seeded
from app.services.booking_service import confirm_booking, create_booking_intent, get_available_times
from app.whatsapp.flow import route_incoming_whatsapp_event


class AvailabilityTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
        self.next_monday = next_monday

        self.service = Service.objects.create(
            name="Bodas",
            slug="",
            internal_code="Service_Boda",
            availability_type=Service.AvailabilityType.PERMANENT,
            default_duration_minutes=60,
            booking_interval_minutes=30,
            is_active=True,
        )
        ServiceWeeklyRange.objects.create(
            service=self.service,
            weekday=0,
            label="Matutino",
            start_time=time(10, 0),
            end_time=time(12, 0),
            order_index=10,
        )
        self.package = ServicePackage.objects.create(
            service=self.service,
            name="Base",
            price=1000,
            deposit_required=300,
            duration_minutes=60,
            is_default=True,
            is_active=True,
            order_index=10,
        )

        self.user = User.objects.create(phone_number="5215500000000", name="Test User")
        create_booking_intent(user=self.user, service=self.service, source_option_key="Service_Boda")

        Booking.objects.create(
            user=self.user,
            service=self.service,
            package=self.package,
            customer_name=self.user.name,
            customer_phone=self.user.phone_number,
            date=next_monday,
            time=time(10, 0),
            duration_minutes=60,
            status=Booking.Status.CONFIRMED,
            source=Booking.Source.WHATSAPP,
        )

    def test_available_times_excludes_booked_slots(self):
        data = get_available_times(
            token=self.user.booking_token,
            target_date=self.next_monday.isoformat(),
            package_id=self.package.id,
        )
        self.assertNotIn("10:00", data["times"])
        self.assertIn("11:00", data["times"])

    def test_booking_fails_outside_service_date_range(self):
        self.service.availability_type = Service.AvailabilityType.TEMPORARY
        self.service.available_from = self.next_monday + timedelta(days=5)
        self.service.available_until = self.next_monday + timedelta(days=20)
        self.service.save(update_fields=["availability_type", "available_from", "available_until", "updated_at"])
        with self.assertRaises(ValidationError):
            confirm_booking(
                token=self.user.booking_token,
                target_date=self.next_monday.isoformat(),
                target_time="11:00",
                package_id=self.package.id,
                customer_name="Cliente",
                customer_phone="5215500000000",
            )


class BotFlowNodeTests(TestCase):
    def test_main_flow_seed_and_routing(self):
        ensure_default_bot_flow_seeded()

        hello_payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [{"from": "5215509999999", "type": "text", "text": {"body": "Hola"}}],
                                "contacts": [{"profile": {"name": "Cliente Nodo"}}],
                            }
                        }
                    ]
                }
            ]
        }
        hello_result = route_incoming_whatsapp_event(data=hello_payload, base_url="http://localhost:8000")
        self.assertIsNotNone(hello_result)
        self.assertGreaterEqual(len(hello_result.payloads), 2)
        self.assertEqual(hello_result.payloads[1]["type"], "interactive")

        agendar_payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "5215509999999",
                                        "type": "interactive",
                                        "interactive": {"list_reply": {"id": "Agendar", "title": "Agendar"}},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        agendar_result = route_incoming_whatsapp_event(data=agendar_payload, base_url="http://localhost:8000")
        self.assertIsNotNone(agendar_result)
        self.assertTrue(agendar_result.payloads)
        self.assertEqual(agendar_result.payloads[0]["type"], "interactive")
