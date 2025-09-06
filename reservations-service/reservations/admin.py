from django.contrib import admin

# Register your models here.
from .models import Reservation, Payment

admin.site.register(Reservation)
admin.site.register(Payment)