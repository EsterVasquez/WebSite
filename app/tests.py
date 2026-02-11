from datetime import date, time, timedelta

from django.test import TestCase
from django.utils import timezone

from app.models import Booking, Day, Service, ServiceTier, TimeBlock, User
from app.services.booking_service import create_booking_intent, get_available_times


class AvailabilityTests(TestCase):
    def setUp(self):
        self.day = Day.objects.create(day="Lunes")
        today = timezone.localdate()
        next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)

        self.service = Service.objects.create(
            name="Bodas",
            payload_id="Service_Boda",
            category="Eventos",
            available_from=today,
            available_until=today + timedelta(days=365),
            is_active=True,
        )
        self.service.days.add(self.day)
        self.tier = ServiceTier.objects.create(
            service=self.service,
            name="Base",
            price=1000,
            duration_minutes=60,
            is_default=True,
        )
        TimeBlock.objects.create(
            service=self.service,
            day=self.day,
            name="Matutino",
            start_time=time(10, 0),
            end_time=time(12, 0),
        )

        self.user = User.objects.create(phone_number="5215500000000", name="Test User")
        create_booking_intent(self.user, self.service, "Service_Boda")

        Booking.objects.create(
            user=self.user,
            service_tier=self.tier,
            date=next_monday,
            time=time(10, 0),
            status="Confirmado",
        )
        self.next_monday = next_monday

    def test_available_times_excludes_booked_slots(self):
        data = get_available_times(
            token=self.user.booking_token,
            target_date=self.next_monday.isoformat(),
            tier_id=self.tier.id,
        )
        self.assertNotIn("10:00", data["times"])
        self.assertIn("11:00", data["times"])
