from django.contrib import admin

# Register your models here.
from .models import User

class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "dni", "phone", "is_staff", "is_superuser", "is_active")
    

admin.site.register(User, UserAdmin)