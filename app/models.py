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


class Day(models.Model):
    id_days = models.AutoField(primary_key=True)
    day = models.CharField(max_length=20, unique=True)  # Ej: Lunes, Martes, etc.

    def __str__(self):
        return self.day
class Service(models.Model):
    name = models.CharField(max_length=100)
    link = models.URLField(blank=True, null=True)
    # Fecha de inicio de disponibilidad
    available_from = models.DateField()
    available_until = models.DateField(
        null=True, blank=True)  # Fecha final opcional
 
    days = models.ManyToManyField(Day, related_name='services')

class ServiceTier(models.Model):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="tiers")
    # Ej: "bara", "meh", "hay plata"
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.service.name} - {self.name}"

# TODO: Agregar los dias especiales para dias en que hay que agendar en ocasiones extradorinarias

class Feriado(models.Model):
    id_feriado = models.AutoField(primary_key=True)
    fecha = models.DateField(unique=True)

    def __str__(self):
        return str(self.fecha)
class TimeBlock(models.Model):
    id_block_time = models.AutoField(primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='time_blocks')
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='time_blocks')
    start_time = models.TimeField()
    end_time = models.TimeField()
    name = models.CharField(max_length=50)  # Ej: Matutino, Vespertino, etc.

    def __str__(self):
        return f"{self.name} - {self.day.day} ({self.start_time}-{self.end_time})"

class AppointmentAvailable(models.Model):
    ESTADO_CHOICES = [
        ('reservado', 'Reservado'),
        ('disponible', 'Disponible'),
    ]

    id_cita = models.AutoField(primary_key=True)
    tier = models.ForeignKey(ServiceTier, on_delete=models.CASCADE, related_name='appointments')
    block_time = models.ForeignKey(TimeBlock, on_delete=models.CASCADE, related_name='appointments')
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')

    def __str__(self):
        return f"{self.tier.nombre} - {self.fecha} ({self.estado})"
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
