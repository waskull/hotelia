from django.db import models

# Create your models here.


class Hotel(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Hoteles"
        verbose_name = "Hotel"
        
    def __str__(self):
        return self.name


class RoomType(models.TextChoices):
    SINGLE = 'single'
    DOUBLE = 'double'
    SQUAD = 'squad'
    SUITE = 'Suite'

class RoomStatus(models.TextChoices):
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"
    AVAILABLE = "available"

class Room(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    room_type = models.CharField(max_length=100, choices=RoomType.choices)
    room_number = models.IntegerField()
    status = models.CharField(max_length=50, default=RoomStatus.AVAILABLE, choices=RoomStatus.choices)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    hotel = models.ForeignKey(
        'Hotel', on_delete=models.CASCADE, related_name='rooms')
    
    class Meta:
        verbose_name_plural = "Habitaciones"
        verbose_name = "Habitación"

    def __str__(self):
        return f"{self.hotel.name} - Hab. {self.room_number}"
