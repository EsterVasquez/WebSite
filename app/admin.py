from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'name', 'last_command')
    search_fields = ('phone_number', 'name')
