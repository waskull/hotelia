from django.db import models

# Create your models here.

class Notification(models.Model):
    class Meta:
        verbose_name_plural = "Notificaciones"
        verbose_name = "Notificación"
        
    user_id = models.IntegerField()
    message = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)