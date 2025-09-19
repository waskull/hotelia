# products-service/authentication.py

import requests
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

# La URL de tu auth-service
GATEWAY_SERVICE_URL = 'http://localhost:8000/auth/me/'


class UserAuthentication(BaseAuthentication):
    def authenticate(self, request):

        try:
            # 1. Realiza una llamada al auth-service para obtener la info del usuario
            headers = {'Authorization': request.headers.get('Authorization')}
            response = requests.get(
                GATEWAY_SERVICE_URL, headers=headers)
            response.raise_for_status()  # Lanza un error para códigos de estado 4xx/5xx

            user_data = response.json()
            user_id = user_data.get('id')
            if not user_id:
                return None  # No hay ID de usuario en el encabezado

            # 2. Crea un objeto de usuario en memoria con la info obtenida

            class ProxyUser(AbstractBaseUser):
                id = None
                username = user_data.get('email')
                email = user_data.get("email")
                is_staff = user_data.get('is_staff', False)
                is_superuser = user_data.get('is_superuser', False)
                first_name = user_data.get('first_name')
                last_name = user_data.get('last_name')
                dni = user_data.get('dni')
                phone = user_data.get('phone')
                is_active = user_data.get('is_active', False)
                groups = user_data.get('groups')

                @property
                def is_authenticated(self):
                    return True

                def get_username(self):
                    return self.email

                def has_perm(self, perm, obj=None):
                    # Lógica de permisos, podrías obtenerla del auth-service
                    return True

                def has_module_perms(self, app_label):
                    return True

            user = ProxyUser()
            user.id = user_id
            return (user, None)

        except requests.exceptions.RequestException:
            # Fallo en la comunicación con el auth-service
            raise AuthenticationFailed(
                "Fallo al comunicarse con el servicio de autenticación.")
        except (ValueError, TypeError, KeyError):
            # Formato de datos incorrecto
            raise AuthenticationFailed(
                "El servicio de autenticación respondio con datos de usuario incorrectos.")
