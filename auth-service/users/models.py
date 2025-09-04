from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from .managers import UserManager

phone_regex = RegexValidator(
    regex=r"\+?1?\d{9,15}$",
    message="Introduce un numero de telefono valido: +999999999. Con un maximo de 17 digitos.",
)
# Create your models here.


class User(AbstractUser):
    email = models.EmailField(
        "email address",
        unique=True,
        error_messages={"unique": "Ya hay un usuario con este email"},
    )
    dni = models.CharField(max_length=10, unique=True)
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=False)
    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["dni"]

    objects = UserManager()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.email}"
    
    class Meta:
        verbose_name_plural = "Usuarios"
        verbose_name = "Usuario"
    
    
