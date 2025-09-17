from django.db import models

# Create your models here.

class Service(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField(default='http://localhost')
    url_production = models.URLField(null=False)
    port = models.IntegerField()

    @property
    def uri(self):
        return f"{self.url}:{self.port}/api/"

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Microservicio'
        verbose_name_plural = 'Microservicios'
    