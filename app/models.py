import uuid

from django.db import models


class User(models.Model):
    class ConversationState(models.TextChoices):
        IDLE = "idle", "Sin estado"
        COTIZAR = "cotizar", "Cotizando"
        AGENDAR = "agendar", "Agendando"

    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    conversation_state = models.CharField(
        max_length=30,
        choices=ConversationState.choices,
        default=ConversationState.IDLE,
    )
    booking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} ({self.name or 'Sin nombre'})"


class Message(models.Model):
    class Direction(models.TextChoices):
        INCOMING = "incoming", "Entrante"
        OUTGOING = "outgoing", "Saliente"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField()
    direction = models.CharField(
        max_length=20,
        choices=Direction.choices,
        default=Direction.INCOMING,
    )
    message_type = models.CharField(max_length=30, default="text")
    payload_id = models.CharField(max_length=120, blank=True, null=True)
    raw_payload = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.phone_number} - {self.direction} - {self.timestamp}"


class BotResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bot_responses")
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]


class Day(models.Model):
    id_days = models.AutoField(primary_key=True)
    day = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.day


class Service(models.Model):
    name = models.CharField(max_length=100)
    payload_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    available_from = models.DateField()
    available_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    days = models.ManyToManyField(Day, related_name="services")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ServiceTier(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="tiers")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.PositiveIntegerField()
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["service__name", "price"]

    def __str__(self):
        return f"{self.service.name} - {self.name}"


class Feriado(models.Model):
    id_feriado = models.AutoField(primary_key=True)
    fecha = models.DateField(unique=True)

    def __str__(self):
        return str(self.fecha)


class TimeBlock(models.Model):
    id_block_time = models.AutoField(primary_key=True)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="time_blocks",
    )
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name="time_blocks")
    start_time = models.TimeField()
    end_time = models.TimeField()
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ["service__name", "day__id_days", "start_time"]

    def __str__(self):
        return f"{self.name} - {self.day.day} ({self.start_time}-{self.end_time})"


class AppointmentAvailable(models.Model):
    ESTADO_CHOICES = [
        ("reservado", "Reservado"),
        ("disponible", "Disponible"),
    ]

    id_cita = models.AutoField(primary_key=True)
    tier = models.ForeignKey(
        ServiceTier,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    block_time = models.ForeignKey(
        TimeBlock,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    fecha = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="disponible",
    )

    def __str__(self):
        return f"{self.tier.name} - {self.fecha} ({self.estado})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ("Pendiente", "Pendiente"),
        ("Confirmado", "Confirmado"),
        ("Cancelado", "Cancelado"),
    ]

    SOURCE_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("dashboard", "Dashboard"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    service_tier = models.ForeignKey(
        ServiceTier,
        on_delete=models.DO_NOTHING,
        related_name="bookings",
    )
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pendiente")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="whatsapp")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time", "-created_at"]

    def __str__(self):
        return f"{self.user.phone_number} - {self.service_tier} - {self.date} {self.time}"


class BookingIntent(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Abierto"
        COMPLETED = "completed", "Completado"
        CANCELLED = "cancelled", "Cancelado"

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booking_intents")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="booking_intents")
    selected_tier = models.ForeignKey(
        ServiceTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_intents",
    )
    source_payload_id = models.CharField(max_length=120)
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
