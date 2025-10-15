from django.db import models


class User(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100)


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class BotResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class Service(models.Model):
    name = models.CharField(max_length=100)
    link = models.URLField(blank=True, null=True)


class ServiceTier(models.Model):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="tiers")
    # Ej: "bara", "meh", "hay plata"
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.PositiveIntegerField()

    valid_hours_start = models.TimeField()
    valid_hours_end = models.TimeField()
    valid_days = models.JSONField(default=list)  # Ej: ["Mon", "Wed"]
    # Fecha de inicio de disponibilidad
    available_from = models.DateField()
    available_until = models.DateField(
        null=True, blank=True)  # Fecha final opcional

    def __str__(self):
        return f"{self.service.name} - {self.name}"

# TODO: Agregar los dias especiales para dias en que hay que agendar en ocasiones extradorinarias

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Confirmado', 'Confirmado'),
        ('Cancelado', 'Cancelado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_tier = models.ForeignKey(ServiceTier, on_delete=models.DO_NOTHING)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pendiente')
