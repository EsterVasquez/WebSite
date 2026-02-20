import uuid

from django.db import models
from django.utils.text import slugify


class User(models.Model):
    class ConversationState(models.TextChoices):
        IDLE = "idle", "Sin estado"
        QUOTE = "quote", "Cotizacion"
        BOOKING = "booking", "Agendado"

    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=120, blank=True, default="")
    conversation_state = models.CharField(
        max_length=20,
        choices=ConversationState.choices,
        default=ConversationState.IDLE,
    )
    booking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    active_flow = models.ForeignKey(
        "BotFlow",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    active_node = models.ForeignKey(
        "BotFlowNode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.phone_number} ({self.name or 'Sin nombre'})"


class Message(models.Model):
    class Direction(models.TextChoices):
        INCOMING = "incoming", "Entrante"
        OUTGOING = "outgoing", "Saliente"

    class SenderRole(models.TextChoices):
        USER = "user", "Usuario"
        BOT = "bot", "Bot"
        AGENT = "agent", "Agente"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField(blank=True, default="")
    direction = models.CharField(max_length=20, choices=Direction.choices)
    sender_role = models.CharField(max_length=20, choices=SenderRole.choices, default=SenderRole.USER)
    message_type = models.CharField(max_length=30, default="text")
    payload_id = models.CharField(max_length=120, blank=True, default="")
    raw_payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.phone_number} [{self.direction}]"


class Service(models.Model):
    class AvailabilityType(models.TextChoices):
        PERMANENT = "permanent", "Permanente"
        TEMPORARY = "temporary", "Temporal"

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    internal_code = models.CharField(max_length=120, unique=True, null=True, blank=True)
    category = models.CharField(max_length=80, blank=True, default="")
    description = models.TextField(blank=True, default="")
    quote_url = models.URLField(blank=True, default="")
    availability_type = models.CharField(
        max_length=20,
        choices=AvailabilityType.choices,
        default=AvailabilityType.PERMANENT,
    )
    available_from = models.DateField(null=True, blank=True)
    available_until = models.DateField(null=True, blank=True)
    default_duration_minutes = models.PositiveIntegerField(default=60)
    booking_interval_minutes = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def _build_unique_slug(self) -> str:
        base_slug = slugify(self.name)[:45] or "servicio"
        candidate = base_slug
        suffix = 2
        while Service.objects.exclude(id=self.id).filter(slug=candidate).exists():
            candidate = f"{base_slug[:40]}-{suffix}"
            suffix += 1
        return candidate

    def save(self, *args, **kwargs):
        self.slug = self._build_unique_slug()
        if self.availability_type == Service.AvailabilityType.PERMANENT:
            self.available_from = None
            self.available_until = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ServiceWeeklyRange(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Lunes"
        TUESDAY = 1, "Martes"
        WEDNESDAY = 2, "Miercoles"
        THURSDAY = 3, "Jueves"
        FRIDAY = 4, "Viernes"
        SATURDAY = 5, "Sabado"
        SUNDAY = 6, "Domingo"

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="weekly_ranges")
    weekday = models.IntegerField(choices=Weekday.choices)
    label = models.CharField(max_length=80, blank=True, default="")
    start_time = models.TimeField()
    end_time = models.TimeField()
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["weekday", "order_index", "start_time"]

    def __str__(self):
        return f"{self.service.name} [{self.get_weekday_display()}] {self.start_time}-{self.end_time}"


class ServiceException(models.Model):
    class ExceptionType(models.TextChoices):
        CLOSED = "closed", "Bloquear fecha"
        SPECIAL_RANGE = "special_range", "Horario especial"
        MAX_BOOKINGS = "max_bookings", "Limite de eventos por fecha"

    class RangeMode(models.TextChoices):
        REPLACE = "replace", "Reemplazar horarios del dia"
        ADD = "add", "Agregar horario adicional"

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="exceptions")
    date = models.DateField()
    exception_type = models.CharField(max_length=20, choices=ExceptionType.choices)
    range_mode = models.CharField(max_length=20, choices=RangeMode.choices, default=RangeMode.REPLACE)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    max_bookings = models.PositiveIntegerField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "id"]

    def __str__(self):
        return f"{self.service.name} - {self.date} ({self.exception_type})"


class ServicePackage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="packages")
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_required = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    available_from = models.DateField(null=True, blank=True)
    available_until = models.DateField(null=True, blank=True)
    max_bookings = models.PositiveIntegerField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order_index = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order_index", "id"]

    def __str__(self):
        return f"{self.service.name} - {self.name}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        CONFIRMED = "confirmed", "Confirmado"
        CANCELLED = "cancelled", "Cancelado"
        DOUBTS = "doubts", "Dudas"

    class Source(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        DASHBOARD = "dashboard", "Panel"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="bookings")
    package = models.ForeignKey(
        ServicePackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    customer_name = models.CharField(max_length=120, blank=True, default="")
    customer_phone = models.CharField(max_length=20, blank=True, default="")
    customer_notes = models.TextField(blank=True, default="")
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.WHATSAPP)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time", "-created_at"]

    def __str__(self):
        return f"{self.service.name} - {self.date} {self.time}"


class BookingIntent(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Abierto"
        COMPLETED = "completed", "Completado"
        CANCELLED = "cancelled", "Cancelado"

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booking_intents")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="booking_intents")
    selected_package = models.ForeignKey(
        ServicePackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_intents",
    )
    source_option_key = models.CharField(max_length=120, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    booking = models.OneToOneField(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intent",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.phone_number} - {self.service.name} ({self.status})"


class ChatConversation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        RESOLVED = "resolved", "Resuelto"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="chat_conversation")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    last_user_message_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "-updated_at"]

    def __str__(self):
        return f"{self.user.phone_number} ({self.status})"


class BotFlow(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "name"]

    def __str__(self):
        return self.name


class BotFlowNode(models.Model):
    class InteractionType(models.TextChoices):
        TEXT_ONLY = "text_only", "Solo texto"
        OPTION_LIST = "option_list", "Menu interactivo"
        URL_BUTTON = "url_button", "Boton con enlace"

    flow = models.ForeignKey(BotFlow, on_delete=models.CASCADE, related_name="nodes")
    key = models.CharField(max_length=120)
    title = models.CharField(max_length=120)
    message_text = models.TextField(blank=True, default="")
    interaction_type = models.CharField(
        max_length=20,
        choices=InteractionType.choices,
        default=InteractionType.TEXT_ONLY,
    )
    menu_title = models.CharField(max_length=120, blank=True, default="")
    menu_description = models.TextField(blank=True, default="")
    menu_button_text = models.CharField(max_length=30, blank=True, default="Ver opciones")
    link_button_text = models.CharField(max_length=40, blank=True, default="")
    link_button_url = models.URLField(blank=True, default="")
    default_next = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="previous_default_nodes",
    )
    is_start = models.BooleanField(default=False)
    is_terminal = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order_index = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order_index", "id"]
        constraints = [
            models.UniqueConstraint(fields=["flow", "key"], name="uniq_flow_node_key"),
        ]

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = f"node_{uuid.uuid4().hex[:10]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.flow.slug}:{self.title}"


class BotFlowOption(models.Model):
    class ActionType(models.TextChoices):
        GO_TO_MESSAGE = "go_to_message", "Ir a otro mensaje"
        QUOTE_SERVICE = "quote_service", "Enviar cotizacion de servicio"
        BOOK_SERVICE = "book_service", "Enviar enlace para agendar"
        OPEN_LINK = "open_link", "Enviar enlace"
        GO_TO_START = "go_to_start", "Volver al inicio"
        CLOSE = "close", "Cerrar conversacion"

    node = models.ForeignKey(BotFlowNode, on_delete=models.CASCADE, related_name="options")
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True, default="")
    trigger_key = models.CharField(max_length=120)
    action_type = models.CharField(max_length=20, choices=ActionType.choices, default=ActionType.GO_TO_MESSAGE)
    next_node = models.ForeignKey(
        BotFlowNode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_options",
    )
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    external_url = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    order_index = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order_index", "id"]
        constraints = [
            models.UniqueConstraint(fields=["node", "trigger_key"], name="uniq_node_option_trigger"),
        ]

    def save(self, *args, **kwargs):
        if not self.trigger_key:
            self.trigger_key = f"opt_{uuid.uuid4().hex[:16]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.node.title} -> {self.title}"
