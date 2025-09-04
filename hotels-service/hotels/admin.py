from django.apps import AppConfig
from django.contrib import admin
from .models import Hotel, Room

# Register your models here.
""" class HotelConfig(AppConfig):
    name = "Hotel"
    verbose_name = "Hoteles"
    

class RoomConfig(AppConfig):
    name = "Habitación"
    verbose_name = "Habitaciones"
 """

class HotelsAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'address', 'description', 'image')

class RoomsAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'room_type', 'room_number', 'price_per_day', 'hotel')

admin.site.register(Hotel,HotelsAdmin)
admin.site.register(Room, RoomsAdmin)