from django.contrib import admin

from app.models import (
    Booking,
    BookingIntent,
    BotResponse,
    Day,
    Feriado,
    Message,
    Service,
    ServiceTier,
    TimeBlock,
    User,
)

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "name", "conversation_state", "booking_token")
    search_fields = ("phone_number", "name")
    list_filter = ("conversation_state",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("user", "direction", "message_type", "payload_id", "timestamp")
    search_fields = ("user__phone_number", "content", "payload_id")
    list_filter = ("direction", "message_type")


@admin.register(BotResponse)
class BotResponseAdmin(admin.ModelAdmin):
    list_display = ("user", "timestamp")
    search_fields = ("user__phone_number", "response")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "payload_id", "category", "available_from", "available_until", "is_active")
    search_fields = ("name", "payload_id", "category")
    list_filter = ("category", "is_active")


@admin.register(ServiceTier)
class ServiceTierAdmin(admin.ModelAdmin):
    list_display = ("service", "name", "price", "duration_minutes", "is_default")
    search_fields = ("service__name", "name")
    list_filter = ("is_default",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("user", "service_tier", "date", "time", "status", "source")
    search_fields = ("user__phone_number", "user__name", "service_tier__service__name")
    list_filter = ("status", "source", "date")


@admin.register(BookingIntent)
class BookingIntentAdmin(admin.ModelAdmin):
    list_display = ("user", "service", "selected_tier", "status", "created_at")
    search_fields = ("user__phone_number", "service__name", "source_payload_id")
    list_filter = ("status", "service__category")


@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ("service", "day", "name", "start_time", "end_time")
    list_filter = ("day", "service")


@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ("day",)


@admin.register(Feriado)
class FeriadoAdmin(admin.ModelAdmin):
    list_display = ("fecha",)
