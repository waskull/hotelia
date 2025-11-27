from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator, MinLengthValidator

# Create your models here.


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Hotel(BaseModel):
    name = models.CharField(max_length=100, unique=True, validators=[MinLengthValidator(2)])
    city = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    address = models.TextField(null=False, validators=[
                               MinLengthValidator(3)])
    description = models.TextField(null=True)
    phone = models.CharField(max_length=40, null=False)
    email = models.EmailField(null=True)
    payment_policy = models.TextField()
    reservation_policy = models.TextField()
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    services = models.TextField(null=True, blank=True)
    star_rating = models.PositiveSmallIntegerField(default=1, validators=[
        MaxValueValidator(5),
        MinValueValidator(1)
    ])

    class Meta:
        verbose_name_plural = "Hoteles"
        verbose_name = "Hotel"

    def __str__(self):
        return self.name


class Review(BaseModel):
    rating = models.PositiveSmallIntegerField(
        validators=[
            MaxValueValidator(5),
            MinValueValidator(1)
        ])
    hotel = models.ForeignKey(
        'Hotel', on_delete=models.CASCADE, related_name='ratings')
    user_id = models.IntegerField(
        help_text="ID del usuario que realizo la reserva.")
    comment = models.TextField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Reseñas"
        verbose_name = "Reseña"

    def __str__(self):
        return f"Reseña de {self.user_id} para el hotel {self.hotel.name}"


class RoomType(models.TextChoices):
    SINGLE = 'single'
    DOUBLE = 'double'
    SQUAD = 'squad'
    SUITE = 'Suite'


class RoomStatus(models.TextChoices):
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"
    AVAILABLE = "available"


class Room(BaseModel):
    capacity = models.IntegerField()
    room_type = models.CharField(max_length=100, choices=RoomType.choices)
    room_number = models.IntegerField()
    status = models.CharField(
        max_length=50, default=RoomStatus.AVAILABLE, choices=RoomStatus.choices)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    hotel = models.ForeignKey(
        'Hotel', on_delete=models.CASCADE, related_name='rooms')

    @property
    def room_name(self):
        return f"Habitación #{self.room_number}"

    class Meta:
        verbose_name_plural = "Habitaciones"
        verbose_name = "Habitación"

    def __str__(self):
        return f"{self.hotel.name} - Hab. {self.room_number}"
