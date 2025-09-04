from django.db import models


class StateStatus(models.TextChoices):
    PENDING = 'pending', 'Reserva Pendiente'
    CONFIRMED = 'confirmed', 'Reserva Confirmada'
    PREPARING = 'preparing', 'Habitación en preparación'
    MAINTENANCE = 'maintenance', 'Habitación en mantenimiento'
    OCUPPIED = 'occupied', 'Ocupada'
    CANCELLED = 'cancelled', 'Reserva Cancelada'


class PaymentMethod(models.TextChoices):
    CASH = 'cash', 'Efectivo'
    DEBIT_CARD = 'debit_card', 'Tarjeta de Debito'
    CREDIT_CARD = 'credit_card', 'Tarjeta de Credito'
    MOBILE_PAYMENT = 'mobile_payment', 'Pago Movil'
    TRANSFER = 'transfer', 'Transferencia Bancaria'

# Create your models here.


class Payment(models.Model):
    class Meta:
        verbose_name_plural = "Pagos"
        verbose_name = "Pago"
        
    reservation = models.ForeignKey(
        'Reservations', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20, default=PaymentMethod.CASH, choices=PaymentMethod.choices)
    payment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Pago de {self.amount} para la reserva {self.reservation}"


class Reservation(models.Model):
    class Meta:
        verbose_name_plural = "Reservas"
        verbose_name = "Reserva"
        
    room_id = models.IntegerField(help_text="ID de la habitación reservada.")
    user_id = models.IntegerField(
        help_text="ID del usuario que realiza la reserva.")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20, default=StateStatus.PENDING, choices=StateStatus.choices)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Reserva de {self.user_id} para la habitación {self.room_id} del {self.start_date} al {self.end_date}"
