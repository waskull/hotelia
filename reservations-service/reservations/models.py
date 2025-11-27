from django.db import models


class Status(models.TextChoices):
    PENDING = 'pending', 'Reserva Pendiente'
    CONFIRMED = 'confirmed', 'Reserva Confirmada'
    PREPARING = 'preparing', 'Habitación en preparación'
    OCUPPIED = 'occupied', 'Ocupada'
    CANCELLED = 'cancelled', 'Reserva Cancelada'
    COMPLETED = 'completed', 'Reserva Completada'


class PaymentMethod(models.TextChoices):
    CASH = 'cash', 'Efectivo'
    DEBIT_CARD = 'debit_card', 'Tarjeta de Debito'
    CREDIT_CARD = 'credit_card', 'Tarjeta de Credito'
    MOBILE_PAYMENT = 'mobile_payment', 'Pago Movil'
    TRANSFER = 'transfer', 'Transferencia Bancaria'

# Create your models here.

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Payment(BaseModel):
    class Meta:
        verbose_name_plural = "Pagos"
        verbose_name = "Pago"
        
    reservation = models.ForeignKey(
        'Reservation', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20, default=PaymentMethod.CASH, choices=PaymentMethod.choices)
    payment_date = models.DateField(auto_now_add=True)
    ref_code = models.CharField(max_length=50, default=None, null=True)

    def __str__(self):
        return f"Pago de {self.amount} para la reserva {self.reservation}"


class Reservation(BaseModel):
    class Meta:
        verbose_name_plural = "Reservas"
        verbose_name = "Reserva"
        
    room_id = models.IntegerField(help_text="ID de la habitación reservada.")
    user_id = models.IntegerField(
        help_text="ID del usuario que realiza la reserva.")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(
        max_length=20, default=Status.PENDING, choices=Status.choices)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Reserva de {self.user_id} para la habitación {self.room_id} del {self.start_date} al {self.end_date}, ID: {self.pk}"
