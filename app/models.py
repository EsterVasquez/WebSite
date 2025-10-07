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
    link = models.URLField()
    anticipated_time = models.PositiveIntegerField()    # In days
    valid_hours_start = models.TimeField()  # Start hour, e.g., 09:00
    # End hour, e.g., 17:00 - Optional
    valid_hours_end = models.TimeField(null=True, blank=True)
    valid_days = models.CharField(max_length=20)  # e.g, Lun, Mar...Vie
    valid_date = models.DateField()  # Start date, e.g., 2023-01-01


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    service = models.ForeignKey(Service, on_delete=models.DO_NOTHING)
    # e.g., Pendiente, Confirmado, Cancelado
    status = models.CharField(max_length=20, default='Pendiente')
