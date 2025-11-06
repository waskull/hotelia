import logging
from json import JSONDecodeError

import httpx
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserRefreshSerializer,
    UserSerializer,
    UpdateUserSerializer,
    UpdateUserPasswordSerializer,
    HotelSerializer,
    RoomSerializer,
    RoomResponseSerializer,
    ReviewSerializer,
    PaymentSerializer,
)


logger = logging.getLogger("gateway")

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

HTTP_TIMEOUT = getattr(settings, "GATEWAY_HTTP_TIMEOUT", 15)
HTTP_MAX_CONNECTIONS = getattr(settings, "GATEWAY_HTTP_MAX_CONNECTIONS", 50)
HTTP_MAX_KEEPALIVE = getattr(settings, "GATEWAY_HTTP_MAX_KEEPALIVE", 10)

#Un cliente global que reutiliza conexiones
CLIENT = httpx.Client(
    timeout=httpx.Timeout(HTTP_TIMEOUT),
    limits=httpx.Limits(max_connections=HTTP_MAX_CONNECTIONS, max_keepalive_connections=HTTP_MAX_KEEPALIVE),
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

class BaseViewSet(ViewSet):
    #Base reutilizable para todos los microservicios del Gateway. Usa sesión httpx global con keepalive y logging.
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
            response = http_client.request(method, url, headers=headers, **kwargs)
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


class AuthView(BaseViewSet):
    SERVICE_URL = settings.USERS_SERVICE_URL

    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", "auth/login/", data=serializer.validated_data)

    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", "auth/register/", data=request.data)

    @action(detail=False, methods=["get"])
    def profile(self, request):
        return self._request("GET", "auth/me/", request=request)
    
class UserRefreshTokenView(BaseViewSet):
    SERVICE_URL = USERS_SERVICE_URL
    serializer_class = UserRefreshSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", "token/refresh/", request=request, json=serializer.validated_data)

class UserView(BaseViewSet):
    SERVICE_URL = USERS_SERVICE_URL
    serializer_class = UserSerializer

    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"auth/{pk}/", request=request)

    def list(self, request, *args, **kwargs):
        return self._request("GET", "auth/", request=request)

    def update(self, request, pk=None, *args, **kwargs):
        serializer = UpdateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("PUT", f"auth/{pk}/", request=request, json=serializer.validated_data)

    def partial_update(self, request, pk=None, *args, **kwargs):
        serializer = UpdateUserPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._request("POST", f"auth/{pk}/password", request=request, json=serializer.validated_data)

    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"auth/{pk}/", request=request)


class HotelView(BaseViewSet):
    SERVICE_URL = HOTELS_SERVICE_URL
    parser_classes = [MultiPartParser, FileUploadParser]
    serializer_class = HotelSerializer

    def list(self, request, *args, **kwargs):
        return self._request("GET", "hotels/", request=request, params=request.query_params)

    def create(self, request, *args, **kwargs):
        headers = {}
        data = {k: v for k, v in request.data.items() if k != "image"}
        files = None
        if "image" in request.FILES:
            image = request.FILES["image"]
            files = {"image": (image.name, image.file, image.content_type)}
            return self._request("POST", "hotels/", request=request, files=files, data=data, headers=headers, timeout=30)


        return self._request("POST", "hotels/", request=request, json=request.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"hotels/{pk}/", request=request)

    def update(self, request, pk=None, *args, **kwargs):
        headers = {}
        data = {k: v for k, v in request.data.items() if k != "image"}
        files = None
        if "image" in request.FILES:
            image = request.FILES["image"]
          
            files = {"image": (image.name, image.file, image.content_type)}
           
            return self._request("PUT", f"hotels/{pk}/", request=request, files=files, data=data, headers=headers, timeout=30)
        

    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"hotels/{pk}/", request=request)

    @action(detail=False, methods=["get"])
    def top(self, request):
        return self._request("GET", "hotels/top/", request=request, params=request.query_params)


class ReviewView(BaseViewSet):
    SERVICE_URL = HOTELS_SERVICE_URL
    serializer_class = ReviewSerializer

    def list(self, request, *args, **kwargs):
        return self._request("GET", "reviews/", request=request, params=request.query_params)

    def create(self, request, *args, **kwargs):
        
        self.SERVICE_TOKEN_HEADER = ("X-Hotel-Gateway-Token", getattr(settings, "HOTEL_SERVICE_TOKEN", ""))
        return self._request("POST", "reviews/", request=request, json=request.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"reviews/{pk}/", request=request)

    def update(self, request, pk=None, *args, **kwargs):
        return self._request("PUT", f"reviews/{pk}/", request=request, json=request.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"reviews/{pk}/", request=request)


class RoomView(BaseViewSet):
    SERVICE_URL = HOTELS_SERVICE_URL
    serializer_class = RoomSerializer

    def list(self, request, *args, **kwargs):
        return self._request("GET", "rooms/", request=request, params=request.query_params)

    def create(self, request, *args, **kwargs):
        return self._request("POST", "rooms/", request=request, json=request.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"rooms/{pk}/", request=request)

    def update(self, request, pk=None, *args, **kwargs):
        return self._request("PUT", f"rooms/{pk}/", request=request, json=request.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"rooms/{pk}/", request=request)


class ReservationView(BaseViewSet):
    SERVICE_URL = RESERVATIONS_SERVICE_URL
    
    SERVICE_TOKEN_HEADER = ("X-Reservation-Gateway-Token", getattr(settings, "RESERVATION_TOKEN", ""))

    def list(self, request, *args, **kwargs):
        return self._request("GET", "reservations/", request=request, params=request.query_params)

    def create(self, request, *args, **kwargs):
        return self._request("POST", "reservations/", request=request, json=request.data, timeout=30)

    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"reservations/{pk}/", request=request)

    @action(detail=True, methods=["get"])
    def payments(self, request, pk=None):
        return self._request("GET", f"reservations/{pk}/payments/", request=request)


    def partial_update(self, request, pk=None, *args, **kwargs):
        return self._request("PATCH", f"reservations/{pk}/", request=request, json=request.data)

    def update(self, request, pk=None, *args, **kwargs):
        return self._request("PUT", f"reservations/{pk}/", request=request, json=request.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"reservations/{pk}/", request=request)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._request("POST", f"reservations/{pk}/cancel/", request=request)


class PaymentView(BaseViewSet):
    SERVICE_URL = RESERVATIONS_SERVICE_URL
    serializer_class = PaymentSerializer
    SERVICE_TOKEN_HEADER = ("X-Reservation-Gateway-Token", getattr(settings, "RESERVATION_TOKEN", ""))

    @action(detail=False, methods=["get"])
    def stats(self, request):
        return self._request("GET", "payments/stats/", request=request)

    def list(self, request, *args, **kwargs):
        return self._request("GET", "payments/", request=request, params=request.query_params)

    def create(self, request, *args, **kwargs):
        return self._request("POST", "payments/", request=request, json=request.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"payments/{pk}/", request=request)

    def update(self, request, pk=None, *args, **kwargs):
        return self._request("PUT", f"payments/{pk}/", request=request, json=request.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        return self._request("DELETE", f"payments/{pk}/", request=request)


class ChatBotView(BaseViewSet):
    SERVICE_URL = CHAT_SERVICE_URL

    def create(self, request, *args, **kwargs):
        return self._request("POST", "llamacpp/", request=request, json=request.data, timeout=1010)

    def retrieve(self, request, pk=None, *args, **kwargs):
        return self._request("GET", f"history/{pk}/", request=request, timeout=12)
    
class OllamaChatBotView(BaseViewSet):
    SERVICE_URL = CHAT_SERVICE_URL

    def create(self, request, *args, **kwargs):
        return self._request("POST", "llama/", request=request, json=request.data, timeout=1010)