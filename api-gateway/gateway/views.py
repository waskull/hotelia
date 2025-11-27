import logging
from json import JSONDecodeError

import httpx
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser, MultiPartParser
# from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .serializers import (
    ReservationSerializer,
    UserRegisterSerializer,
    UserLoginSerializer,
    UserRefreshSerializer,
    UserSerializer,
    UpdateUserSerializer,
    UpdateUserPasswordSerializer,
    UserProfileResponseSerializer,
    UserLogoutSerializer,
    HotelSerializer,
    CreateReservationSerializer,
    UpdateReservationSerializer,
    ExtendReservationSerializer,
    RoomSerializer,
    RoomResponseSerializer,
    ReviewSerializer,
    PaymentSerializer,
    ChatRequestSerializer,
)

from .auth_schemes import ExternalServiceAuthentication

# Asegúrate de que 'ExternalBearerAuth' es el 'name' definido en tu OpenApiAuthenticationExtension
SECURITY_SCHEME_NAME = 'ExternalBearerAuth'


logger = logging.getLogger("gateway")

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

HTTP_TIMEOUT = getattr(settings, "GATEWAY_HTTP_TIMEOUT", 15)
HTTP_MAX_CONNECTIONS = getattr(settings, "GATEWAY_HTTP_MAX_CONNECTIONS", 50)
HTTP_MAX_KEEPALIVE = getattr(settings, "GATEWAY_HTTP_MAX_KEEPALIVE", 10)

# Un cliente global que reutiliza conexiones
CLIENT = httpx.Client(
    timeout=httpx.Timeout(HTTP_TIMEOUT),
    limits=httpx.Limits(max_connections=HTTP_MAX_CONNECTIONS,
                        max_keepalive_connections=HTTP_MAX_KEEPALIVE),
)


USERS_SERVICE_URL = settings.USERS_SERVICE_URL
HOTELS_SERVICE_URL = settings.HOTELS_SERVICE_URL
RESERVATIONS_SERVICE_URL = settings.RESERVATIONS_SERVICE_URL
CHAT_SERVICE_URL = getattr(settings, "CHATBOT_SERVICE_URL", None)


def get_auth_header_from_request(request):
    auth = request.headers.get("Authorization")
    return {"Authorization": auth} if auth else {}


def _build_url(base: str, path: str) -> str:
    if not base.endswith("/") and not path.startswith("/"):
        return f"{base}/{path}"
    return f"{base}{path}"


def _safe_parse_json(response: httpx.Response):
    try:
        return response.json()
    except JSONDecodeError:
        return {"raw": response.text}


http_client = httpx.Client(
    timeout=settings.HTTP_TIMEOUT if hasattr(settings, "HTTP_TIMEOUT") else 15,
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
)


@extend_schema(
    auth=[],
    #    auth=[] significa "ningún esquema de seguridad requerido".
    methods=['GET'],
)
class BaseViewSet(ViewSet):
    # Base reutilizable para todos los microservicios del Gateway. Usa sesión httpx global con keepalive y logging.
    SERVICE_URL = None

    def get_headers(self, request):
        auth = request.headers.get("Authorization")
        headers = {}

        if auth and isinstance(auth, str):
            auth = auth.strip()
            if " " not in auth:
                logger.warning(f"Encabezado Authorization inválido: '{auth}'")
            headers["Authorization"] = auth

        return headers

    def _request(self, method, endpoint, request=None, **kwargs):
        url = f"{self.SERVICE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = kwargs.pop("headers", {})

        if request:
            headers.update(self.get_headers(request))

        try:
            logger.info(f"{method.upper()} {url}")
            response = http_client.request(
                method, url, headers=headers, **kwargs)
            logger.info(f"{response.status_code} {url}")

            try:
                data = response.json()
            except ValueError:
                data = {"detail": response.text}

            return Response(data, status=response.status_code)

        except httpx.RequestError as e:
            logger.error(f"Error de red al contactar {url}: {e}")
            return Response(
                {"error": f"No se pudo contactar el servicio: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.exception(f"Error inesperado al contactar {url}: {e}")
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    auth=[],
    methods=['POST'],
    summary="Login de usuarios",
)
class AuthLoginView(BaseViewSet):
    SERVICE_URL = settings.USERS_SERVICE_URL
    serializer_class = UserLoginSerializer

    @extend_schema(summary="Inicio de sesión de usuario")
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", "auth/login/", request=request, json=serializer.validated_data)


class AuthRegisterView(BaseViewSet):
    SERVICE_URL = settings.USERS_SERVICE_URL
    serializer_class = UserRegisterSerializer

    @extend_schema(summary="Registro de usuarios")
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", "auth/register/", request=request, json=serializer.validated_data)


class AuthProfileView(BaseViewSet):
    SERVICE_URL = settings.USERS_SERVICE_URL

    @extend_schema(
        responses=UserProfileResponseSerializer,
        summary="Obtiene el perfil del usuario autenticado")
    @action(detail=False, methods=["post"])
    def profile(self, request):
        return self._request("post", "auth/me/", request=request)


class UserRefreshTokenView(BaseViewSet):
    SERVICE_URL = USERS_SERVICE_URL
    serializer_class = UserRefreshSerializer

    @extend_schema(summary="Renovación del token de acceso")
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", "auth/refresh/", request=request, json=serializer.validated_data)

class UserLogoutTokenView(BaseViewSet):
    SERVICE_URL = USERS_SERVICE_URL
    serializer_class = UserLogoutSerializer

    @extend_schema(summary="Cerrar sesión del usuario")
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", "auth/logout/", request=request, json=serializer.validated_data)


class UserView(BaseViewSet):
    SERVICE_URL = USERS_SERVICE_URL
    serializer_class = UserSerializer

    @extend_schema(summary="Obtiene los detalles de un usuario")
    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"auth/{pk}/", request=request)

    @extend_schema(summary="Obtiene la lista de usuarios")
    def list(self, request, *args, **kwargs):
        return self._request("GET", "auth/", request=request)

    @extend_schema(summary="Actualiza los detalles de un usuario")
    def update(self, request, pk=None, *args, **kwargs):
        serializer = UpdateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("PUT", f"auth/{pk}/", request=request, json=serializer.validated_data)

    @extend_schema(summary="Actualiza la contraseña de un usuario")
    def partial_update(self, request, pk=None, *args, **kwargs):
        serializer = UpdateUserPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", f"auth/{pk}/password", request=request, json=serializer.validated_data)

    @extend_schema(summary="Elimina un usuario")
    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"auth/{pk}/", request=request)


class HotelView(BaseViewSet):
    SERVICE_URL = HOTELS_SERVICE_URL
    parser_classes = [MultiPartParser, FileUploadParser]
    serializer_class = HotelSerializer

    def get_serializer(self):
        if self.action == "top":
            return None
        return self.serializer_class

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='city',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Introduce una ciudad para filtrar los hoteles',
                required=False,
            ),
        ],
        summary="Obtiene la lista de hoteles"
    )
    def list(self, request, *args, **kwargs):
        return self._request("GET", "hotels/", request=request, params=request.query_params)

    @extend_schema(summary="Crea un hotel")
    def create(self, request, *args, **kwargs):
        headers = {}
        data = {k: v for k, v in request.data.items() if k != "image"}
        files = None
        if "image" in request.FILES:
            image = request.FILES["image"]
            files = {"image": (image.name, image.file, image.content_type)}
            return self._request("POST", "hotels/", request=request, files=files, data=data, headers=headers, timeout=30)

        return self._request("POST", "hotels/", request=request, json=request.data)

    @extend_schema(summary="Obtiene los detalles de un hotel")
    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"hotels/{pk}/", request=request)

    @extend_schema(summary="Actualiza los detalles de un hotel")
    def update(self, request, pk=None, *args, **kwargs):
        headers = {}
        data = {k: v for k, v in request.data.items() if k != "image"}
        files = None
        if "image" in request.FILES:
            image = request.FILES["image"]

            files = {"image": (image.name, image.file, image.content_type)}

            return self._request("PUT", f"hotels/{pk}/", request=request, files=files, data=data, headers=headers, timeout=30)

    @extend_schema(summary="Elimina un hotel")
    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"hotels/{pk}/", request=request)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='global',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='true para traer el top global de hoteles, false para solo el del usuario autenticado.',
                required=False,
            ),
        ],
        summary="Obtiene el top de hoteles"
    )
    @action(detail=False, methods=["POST"])
    def top(self, request):
        return self._request("GET", "hotels/top/", request=request, params=request.query_params)


class ReviewView(BaseViewSet):
    SERVICE_URL = HOTELS_SERVICE_URL
    serializer_class = ReviewSerializer

    @extend_schema(summary="Obtiene la lista de reseñas")
    def list(self, request, *args, **kwargs):
        return self._request("GET", "reviews/", request=request, params=request.query_params)

    @extend_schema(summary="Crea una reseña")
    def create(self, request, *args, **kwargs):

        self.SERVICE_TOKEN_HEADER = (
            "X-Hotel-Gateway-Token", getattr(settings, "HOTEL_SERVICE_TOKEN", ""))
        return self._request("POST", "reviews/", request=request, json=request.data)

    @extend_schema(summary="Obtiene los detalles de una reseña")
    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"reviews/{pk}/", request=request)

    @extend_schema(summary="Actualiza los detalles de una reseña")
    def update(self, request, pk=None, *args, **kwargs):
        return self._request("PUT", f"reviews/{pk}/", request=request, json=request.data)

    @extend_schema(summary="Elimina una reseña")
    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"reviews/{pk}/", request=request)


class RoomView(BaseViewSet):
    SERVICE_URL = HOTELS_SERVICE_URL
    serializer_class = RoomSerializer

    def get_serializer(self):
        if self.action == "top_rooms":
            return None
        return self.serializer_class
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='global',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='true para traer el top global de habitaciones, false para solo el del usuario autenticado.',
                required=False,
            ),
        ],
        summary="Obtiene el top de habitaciones"
    )
    @action(detail=False, methods=["POST"])
    def top_rooms(self, request):
        return self._request("GET", "rooms/top_rooms/", request=request, params=request.query_params)


    @extend_schema(summary="Obtiene la lista de habitaciones")
    def list(self, request, *args, **kwargs):
        return self._request("GET", "rooms/", request=request, params=request.query_params)

    @extend_schema(summary="Crea una habitación")
    def create(self, request, *args, **kwargs):
        return self._request("POST", "rooms/", request=request, json=request.data)

    @extend_schema(summary="Obtiene los detalles de una habitación")
    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"rooms/{pk}/", request=request)

    @extend_schema(summary="Actualiza los detalles de una habitación")
    def update(self, request, pk=None, *args, **kwargs):
        return self._request("PUT", f"rooms/{pk}/", request=request, json=request.data)

    @extend_schema(summary="Elimina una habitación")
    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"rooms/{pk}/", request=request)


class ReservationView(BaseViewSet):
    SERVICE_URL = RESERVATIONS_SERVICE_URL
    SERVICE_TOKEN_HEADER = ("X-Reservation-Gateway-Token",
                            getattr(settings, "RESERVATION_TOKEN", ""))

    def get_serializer_class(self):
        if self.action == "create":
            return CreateReservationSerializer
        if self.action == "update":
            return UpdateReservationSerializer
        if self.action == "extend":
            return ExtendReservationSerializer
        return None

    @extend_schema(summary="Obtiene la lista de reservas")
    def list(self, request, *args, **kwargs):
        return self._request("GET", "reservations/", request=request, params=request.query_params)

    @extend_schema(summary="Crea una reserva")
    def create(self, request, *args, **kwargs):
        serializer = CreateReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", "reservations/", request=request, json=serializer.data, timeout=30)

    @extend_schema(summary="Obtiene los detalles de una reserva")
    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"reservations/{pk}/", request=request)

    @extend_schema(summary="Actualiza los detalles de una reserva")
    def update(self, request, pk=None, *args, **kwargs):
        return self._request("PUT", f"reservations/{pk}/", request=request, json=request.data)

    @extend_schema(summary="Obtiene la lista de pagos de una reservación")
    @action(detail=True, methods=["get"])
    def payments(self, request, pk=None):
        return self._request("GET", f"reservations/{pk}/payments/", request=request)

    @extend_schema(summary="Elimina una reservación")
    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"reservations/{pk}/", request=request)

    @extend_schema(summary="Obtiene la lista de reservas del usuario logeado")
    @action(detail=False, methods=["POST"])
    def user(self, request):
        return self._request("GET", f"reservations/user/", request=request)

    # @action(detail=False, methods=["POST"])
    # def top(self, request):
    #     return self._request("GET", f"reservations/top/", request=request)

    @extend_schema(summary="Modifica el estado de la reservación")
    def partial_update(self, request, pk=None, *args, **kwargs):
        return self._request("PATCH", f"reservations/{pk}/", request=request, json=request.data)

    @extend_schema(summary="Elimina una reservación")
    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"reservations/{pk}/", request=request)

    @extend_schema(summary="Cancela una reservación")
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._request("POST", f"reservations/{pk}/cancel/", request=request)

    @extend_schema(summary="Extiende la fecha de salida de una reservación")
    @action(detail=True, methods=["post"])
    def extend(self, request, pk=None):
        serializer = ExtendReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", f"reservations/{pk}/extend_reservation/", request=request, json=serializer.data)


class PaymentView(BaseViewSet):
    SERVICE_URL = RESERVATIONS_SERVICE_URL
    serializer_class = PaymentSerializer
    SERVICE_TOKEN_HEADER = ("X-Reservation-Gateway-Token",
                            getattr(settings, "RESERVATION_TOKEN", ""))

    @extend_schema(summary="Estadísticas de pagos")
    @action(detail=False, methods=["get"])
    def stats(self, request):
        return self._request("GET", "payments/stats/", request=request)

    @extend_schema(summary="Obtiene la lista de pagos")
    def list(self, request, *args, **kwargs):
        return self._request("GET", "payments/", request=request, params=request.query_params)

    @extend_schema(summary="Crea un pago")
    def create(self, request, *args, **kwargs):
        return self._request("POST", "payments/", request=request, json=request.data)

    @extend_schema(summary="Obtiene los detalles de un pago")
    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"payments/{pk}/", request=request)

    @extend_schema(summary="Actualiza los detalles de un pago")
    def update(self, request, pk=None, *args, **kwargs):
        return self._request("PUT", f"payments/{pk}/", request=request, json=request.data)

    @extend_schema(summary="Elimina un pago")
    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"payments/{pk}/", request=request)


class ChatBotView(BaseViewSet):
    SERVICE_URL = CHAT_SERVICE_URL
    serializer_class = ChatRequestSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return ChatRequestSerializer
        return None

    @extend_schema(summary="Realiza una petición a un LLM/SLM local usando llama.cpp")
    def create(self, request, *args, **kwargs):
        return self._request("POST", "llamacpp/", request=request, json=request.data, timeout=1010)

    @extend_schema(
        # parameters=[
        #     OpenApiParameter(
        #         name='search',
        #         type=OpenApiTypes.STR,
        #         location=OpenApiParameter.QUERY,
        #         description='Para buscar en la conversación de llama.cpp',
        #         required=False,
        #     ),
        # ],
        summary="Obtiene las peticiones y las respuestas del usuario con llama.cpp"
    )
    @action(detail=False, methods=["post"])
    def history(self, request):
        return self._request("GET", "llamacpp/", request=request, timeout=12, params=request.query_params)


class GeminiChatBotView(BaseViewSet):
    SERVICE_URL = CHAT_SERVICE_URL
    serializer_class = ChatRequestSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return ChatRequestSerializer
        return None

    @extend_schema(
        # parameters=[
        #     OpenApiParameter(
        #         name='search',
        #         type=OpenApiTypes.STR,
        #         location=OpenApiParameter.QUERY,
        #         description='Para buscar en la conversación de gemini',
        #         required=False,
        #     ),
        # ],
        summary="Obtiene las peticiones y las respuestas del usuario"
    )
    @action(detail=False, methods=["post"])
    def history(self, request):
        return self._request("GET", "gemini/", request=request, timeout=12, params=request.query_params)

    @extend_schema(
        summary="Realiza una petición al chatbot usando Gemini Flash",
    )
    def create(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", "gemini/", request=request, json=serializer.validated_data, timeout=60)


class OllamaChatBotView(BaseViewSet):
    SERVICE_URL = CHAT_SERVICE_URL
    serializer_class = ChatRequestSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return ChatRequestSerializer
        return None

    @extend_schema(summary="Realiza una petición a un LLM/SLM local usando Ollama")
    def create(self, request, *args, **kwargs):
        return self._request("POST", "ollama/", request=request, json=request.data, timeout=1010)

    @extend_schema(
        # parameters=[
        #     OpenApiParameter(
        #         name='search',
        #         type=OpenApiTypes.STR,
        #         location=OpenApiParameter.QUERY,
        #         description='Para buscar en la conversación de ollama',
        #         required=False,
        #     ),
        # ],
        summary="Obtiene las peticiones y las respuestas del usuario"
    )
    @action(detail=False, methods=["post"])
    def history(self, request):
        return self._request("GET", "ollama/", request=request, timeout=12, params=request.query_params)
