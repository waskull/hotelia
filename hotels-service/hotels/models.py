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


class Room(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    room_type = models.CharField(max_length=100)
    room_number = models.IntegerField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    hotel = models.ForeignKey(
        'Hotel', on_delete=models.CASCADE, related_name='rooms')
    
    class Meta:
        verbose_name_plural = "Habitaciones"
        verbose_name = "Habitación"

    def __str__(self):
        return f"{self.hotel.name} - Hab. {self.room_number}"
