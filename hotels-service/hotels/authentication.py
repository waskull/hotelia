import httpx
import json
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.conf import settings

_client = httpx.Client(base_url=settings.AUTH_SERVICE_URL, timeout=7.0)


class UserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if request.method == 'GET':
            return (AnonymousUser(), None)
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        try:
            # 1. Realiza una llamada al auth-service para obtener la info del usuario
            headers = {'Authorization': auth_header}
            response =  _client.post("auth/me/", headers=headers)
            response.raise_for_status()  # Lanza un error para códigos de estado 4xx/5xx

            try:
                user_data = response.json()
            except json.JSONDecodeError:
                raise AuthenticationFailed(
                    "El servicio de autenticación devolvió una respuesta JSON inválida."
                )
            user_id = user_data.get('id')
            if not user_id:
                return None  # No hay ID de usuario en el encabezado
            
            is_active = user_data.get('is_active', False)
            if not is_active:
                raise AuthenticationFailed(
                    "La solicitud fue rechazada. El usuario no esta activo."
                )

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

        except httpx.RequestError as exc:
            raise AuthenticationFailed(
                "Fallo al comunicarse con el servicio de autenticación."
            )
        except httpx.HTTPStatusError as exc:
            # Por ejemplo: 401 Unauthorized, 403 Forbidden, 500 Internal Server Error
            # Podrías loggear response.text aquí para depuración
            raise AuthenticationFailed(
                f"El servicio de autenticación rechazó la solicitud: {exc.response.status_code}"
            )
        except (ValueError, TypeError, KeyError) as exc:
            raise AuthenticationFailed(
                "El servicio de autenticación respondió con datos de usuario incorrectos."
            )
