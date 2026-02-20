from django.contrib import admin

from app.models import (
    Booking,
    BookingIntent,
    BotFlow,
    BotFlowNode,
    BotFlowOption,
    ChatConversation,
    Message,
    Service,
    ServiceException,
    ServicePackage,
    ServiceWeeklyRange,
    User,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "name", "conversation_state", "booking_token")
    search_fields = ("phone_number", "name")
    list_filter = ("conversation_state",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("user", "direction", "sender_role", "message_type", "payload_id", "created_at")
    search_fields = ("user__phone_number", "content", "payload_id")
    list_filter = ("direction", "sender_role", "message_type")


class ServiceWeeklyRangeInline(admin.TabularInline):
    model = ServiceWeeklyRange
    extra = 0


class ServiceExceptionInline(admin.TabularInline):
    model = ServiceException
    extra = 0


class ServicePackageInline(admin.TabularInline):
    model = ServicePackage
    extra = 0


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "availability_type", "is_active")
    search_fields = ("name", "category", "internal_code")
    list_filter = ("availability_type", "is_active")
    inlines = [ServiceWeeklyRangeInline, ServiceExceptionInline, ServicePackageInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("service", "package", "customer_name", "customer_phone", "date", "time", "status", "source")
    search_fields = ("customer_name", "customer_phone", "service__name", "user__phone_number")
    list_filter = ("status", "source", "date")


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "last_user_message_at", "resolved_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("user__phone_number", "user__name")


@admin.register(BookingIntent)
class BookingIntentAdmin(admin.ModelAdmin):
    list_display = ("user", "service", "selected_package", "status", "created_at")
    search_fields = ("user__phone_number", "service__name", "source_option_key")
    list_filter = ("status", "service__category")


class BotFlowOptionInline(admin.TabularInline):
    model = BotFlowOption
    fk_name = "node"
    extra = 0
    fields = ("order_index", "title", "trigger_key", "action_type", "next_node", "service", "is_active")
    readonly_fields = ("trigger_key",)


@admin.register(BotFlowNode)
class BotFlowNodeAdmin(admin.ModelAdmin):
    list_display = ("flow", "title", "key", "interaction_type", "is_start", "is_terminal", "is_active")
    search_fields = ("title", "key", "flow__name")
    list_filter = ("interaction_type", "is_start", "is_terminal", "is_active")
    inlines = [BotFlowOptionInline]
    readonly_fields = ("key",)


@admin.register(BotFlow)
class BotFlowAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "is_published", "updated_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active", "is_published")
