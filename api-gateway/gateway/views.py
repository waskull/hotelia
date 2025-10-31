import httpx
from json import JSONDecodeError
#from asgiref.sync import async_to_sync
from django.conf import settings
# from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FileUploadParser
from .serializers import *
# Create your views here.
USERS_SERVICE_URL = settings.USERS_SERVICE_URL
HOTELS_SERVICE_URL = settings.HOTELS_SERVICE_URL
RESERVATIONS_SERVICE_URL = settings.RESERVATIONS_SERVICE_URL
CHAT_SERVICE_URL = settings.CHATBOT_SERVICE_URL

def getHeaders(request):
    return {'Authorization': request.headers.get(
        'Authorization')}

class UserRegisterView(ViewSet):
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            response = httpx.post(
                f'{USERS_SERVICE_URL}auth/', json=request.data, timeout=12)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserLoginView(ViewSet):
    serializer_class = UserLoginSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            response = httpx.post(
                f'{USERS_SERVICE_URL}auth/login/', json=serializer.data)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserRefreshTokenView(ViewSet):
    serializer_class = UserRefreshSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            response = httpx.post(
                f'{USERS_SERVICE_URL}token/refresh/', json=serializer.data)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserProfileView(ViewSet):
    # permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def list(self, request, format=None):
        headers = getHeaders(request)
        try:
            response = httpx.get(
                f'{USERS_SERVICE_URL}auth/me/', headers=headers, timeout=12)
            serializer = self.serializer_class(data=response.json())
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=response.status_code)

        except httpx.RequestError as e:
            print("Error: ", response.status_code)
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserView(ViewSet):
    # permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        print("Headers: ", headers)
        try:
            response = httpx.get(
                f'{USERS_SERVICE_URL}auth/{pk}/', headers=headers)
            serializer = self.serializer_class(data=response.json())
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.get(
                f'{USERS_SERVICE_URL}auth/', headers=headers)
            serializer = self.serializer_class(data=response.json(), many=True)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=response.status_code)
        except httpx.RequestError as e:
            print("Error: ", response.status_code)
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)        

    def update(self, request, pk, *args, **kwargs):
        serializer = UpdateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        headers = getHeaders(request)
        try:
            response = httpx.put(
                f'{USERS_SERVICE_URL}auth/{pk}/', json=serializer.validated_data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    def partial_update(self, request, pk, *args, **kwargs):        
        serializer = UpdateUserPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        headers = getHeaders(request)
        try:
            response = httpx.post(
                f'{USERS_SERVICE_URL}auth/{pk}/password', json=serializer.validated_data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def destroy(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.delete(
                f'{USERS_SERVICE_URL}auth/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class HotelView(ViewSet):
    # permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FileUploadParser]
    serializer_class = HotelSerializer

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.get(
                f'{HOTELS_SERVICE_URL}hotels/', timeout=15, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except JSONDecodeError as e:
            print(e)
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def create(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            data_without_image = {
                'name': request.data['name'],
                'city': request.data['city'],
                'address': request.data['address'],
                'description': request.data['description'],
                'services': request.data['services']
            }
            image_file = request.FILES['image']
            files = {
                'image': (image_file.name, image_file.read(), image_file.content_type)}
            response = httpx.post(
                f'{HOTELS_SERVICE_URL}hotels/', timeout=15, files=files, data=data_without_image, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.get(
                f'{HOTELS_SERVICE_URL}hotels/{pk}/', timeout=15, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.put(
                f'{HOTELS_SERVICE_URL}hotels/{pk}/', timeout=15, json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def destroy(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.delete(
                f'{HOTELS_SERVICE_URL}hotels/{pk}/', timeout=15, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    @action(detail=False, methods=["get"])
    def top(self, request):
        headers = getHeaders(request)
        url = f'{HOTELS_SERVICE_URL}hotels/top/'
        try:
            response = httpx.get(url, params=request.query_params,headers=headers, timeout=15)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            print(e)
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['GET'])
async def top(request):
        headers = getHeaders(request)
        url = f'{HOTELS_SERVICE_URL}hotels/top/'
        #try:
        print(url)
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=request.query_params, headers=headers, timeout=15)
            print(response.json())
            try:
                return Response(response.json(), status=response.status_code)
            except httpx.RequestError as e:
                return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ReviewView(ViewSet):
    serializer_class = ReviewSerializer

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.get(
                f'{HOTELS_SERVICE_URL}reviews/', timeout=15, headers=headers, params=request.query_params)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def create(self, request, *args, **kwargs):
        headers = getHeaders(request)
        headers["X-Hotel-Gateway-Token"] = settings.HOTEL_SERVICE_TOKEN
        try:
            print(headers)
            response = httpx.post(
                f'{HOTELS_SERVICE_URL}reviews/', timeout=15, json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.get(
                f'{HOTELS_SERVICE_URL}reviews/{pk}/', timeout=15, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.put(
                f'{HOTELS_SERVICE_URL}reviews/{pk}/', timeout=15, json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def destroy(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.delete(
                f'{HOTELS_SERVICE_URL}reviews/{pk}/', timeout=15, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class RoomView(ViewSet):
    # permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializer

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.get(
                f'{HOTELS_SERVICE_URL}rooms/', timeout=15, headers=headers)
            serializer = RoomResponseSerializer(data=response.json(), many=True)
            serializer.is_valid()
            return Response(serializer.validated_data, status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def create(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.post(
                f'{HOTELS_SERVICE_URL}rooms/', timeout=15, json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.get(
                f'{HOTELS_SERVICE_URL}rooms/{pk}/', timeout=15, headers=headers)
            serializer = RoomResponseSerializer(data=response.json(), many=False)
            serializer.is_valid()
            return Response(serializer.validated_data, status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.put(
                f'{HOTELS_SERVICE_URL}rooms/{pk}/', timeout=15, json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def destroy(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.delete(
                f'{HOTELS_SERVICE_URL}rooms/{pk}/', timeout=15, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ReservationView(ViewSet):
    # permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        headers["X-Reservation-Gateway-Token"] = settings.RESERVATION_TOKEN
        try:
            response = httpx.get(
                f'{RESERVATIONS_SERVICE_URL}reservations/', timeout=15, headers=headers, params=request.query_params)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def create(self, request, *args, **kwargs):
        headers = getHeaders(request)
        headers["X-Reservation-Gateway-Token"] = settings.RESERVATION_TOKEN
        try:
            response = httpx.post(
                f'{RESERVATIONS_SERVICE_URL}reservations/', timeout=20, json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        headers["X-Reservation-Gateway-Token"] = settings.RESERVATION_TOKEN
        try:
            response = httpx.get(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', timeout=15, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=True, methods=["get"])
    def payments(self, request, pk=None):
        headers = getHeaders(request)
        headers["X-Reservation-Gateway-Token"] = settings.RESERVATION_TOKEN
        try:
            response = httpx.get(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/payments/', timeout=15, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def partial_update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        headers["X-Reservation-Gateway-Token"] = settings.RESERVATION_TOKEN
        try:
            response = httpx.patch(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', timeout=15, json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        headers["X-Reservation-Gateway-Token"] = settings.RESERVATION_TOKEN
        try:
            response = httpx.put(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', timeout=15, json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def destroy(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        headers["X-Reservation-Gateway-Token"] = settings.RESERVATION_TOKEN
        try:
            response = httpx.delete(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', timeout=15, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class PaymentView(ViewSet):
    # permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    @action(detail=False, methods=["get"])
    def stats(self, request):
        headers = getHeaders(request)
        headers["X-Reservation-Gateway-Token"] = settings.RESERVATION_TOKEN
        try:
            response = httpx.get(
                f'{RESERVATIONS_SERVICE_URL}payments/stats/', headers=headers)
            print(response.json())
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.get(
                f'{RESERVATIONS_SERVICE_URL}payments/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def create(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.post(
                f'{RESERVATIONS_SERVICE_URL}payments/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.get(
                f'{RESERVATIONS_SERVICE_URL}payments/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.put(
                f'{RESERVATIONS_SERVICE_URL}payments/{pk}/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def destroy(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.delete(
                f'{RESERVATIONS_SERVICE_URL}payments/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class ChatBotView(ViewSet):
    def create(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = httpx.post(
                f'{CHAT_SERVICE_URL}llama/', json=request.data, headers=headers, timeout=1010)
            return Response(response.json(), status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)