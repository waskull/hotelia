import requests
from django.shortcuts import render
# from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FileUploadParser
from .serializers import UserSerializer, UserLoginSerializer, UserRefreshSerializer, UserRegisterSerializer, HotelSerializer, RoomSerializer, ReservationSerializer, PaymentSerializer
# Create your views here.
USERS_SERVICE_URL = 'http://localhost:8001/api/'
HOTELS_SERVICE_URL = 'http://localhost:8002/api/'
RESERVATIONS_SERVICE_URL = 'http://localhost:8003/api/'


def getHeaders(request):
    headers = {'Authorization': request.headers.get(
        'Authorization')}
    return headers


class UserRegisterView(ViewSet):
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            response = requests.post(
                f'{USERS_SERVICE_URL}auth/', json=request.data)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserLoginView(ViewSet):
    serializer_class = UserLoginSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            response = requests.post(
                f'{USERS_SERVICE_URL}auth/login/', json=serializer.data)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserRefreshTokenView(ViewSet):
    serializer_class = UserRefreshSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            response = requests.post(
                f'{USERS_SERVICE_URL}token/refresh/', json=serializer.data)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserDetailView(ViewSet):
    # permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        print("Headers: ", headers)
        try:
            response = requests.get(
                f'{USERS_SERVICE_URL}auth/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserProfileView(ViewSet):
    # permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.get(
                f'{USERS_SERVICE_URL}auth/me/', headers=headers)
            serializer = self.serializer_class(data=response.json())
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=response.status_code)
        except requests.exceptions.RequestException as e:
            print("Error: ", response.status_code)
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class HotelView(ViewSet):
    # permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FileUploadParser]
    serializer_class = HotelSerializer

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.get(
                f'{HOTELS_SERVICE_URL}hotels/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def create(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            data_without_image = {
                'name': request.data['name'],
                'city': request.data['city'],
                'address': request.data['address'],
                'description': request.data['description']
            }
            image_file = request.FILES['image']
            files = {
                'image': (image_file.name, image_file.read(), image_file.content_type)}
            response = requests.post(
                f'{HOTELS_SERVICE_URL}hotels/', files=files, data=data_without_image, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.get(
                f'{HOTELS_SERVICE_URL}hotels/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.put(
                f'{HOTELS_SERVICE_URL}hotels/{pk}/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def destroy(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.delete(
                f'{HOTELS_SERVICE_URL}hotels/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class RoomView(ViewSet):
    # permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializer

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.get(
                f'{HOTELS_SERVICE_URL}rooms/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def create(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.post(
                f'{HOTELS_SERVICE_URL}rooms/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.get(
                f'{HOTELS_SERVICE_URL}rooms/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.put(
                f'{HOTELS_SERVICE_URL}rooms/{pk}/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def destroy(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.delete(
                f'{HOTELS_SERVICE_URL}rooms/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ReservationView(ViewSet):
    # permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.get(
                f'{RESERVATIONS_SERVICE_URL}reservations/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def create(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.post(
                f'{RESERVATIONS_SERVICE_URL}reservations/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.get(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=True, methods=["get"])
    def payments(self, request, pk=None):
        headers = getHeaders(request)
        try:
            response = requests.get(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/payments/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def partial_update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.patch(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return  Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    def update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.put(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return  Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def destroy(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.delete(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class PaymentView(ViewSet):
    # permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def list(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.get(
                f'{RESERVATIONS_SERVICE_URL}payments/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def create(self, request, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.post(
                f'{RESERVATIONS_SERVICE_URL}payments/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def retrieve(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.get(
                f'{RESERVATIONS_SERVICE_URL}payments/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def update(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.put(
                f'{RESERVATIONS_SERVICE_URL}payments/{pk}/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def destroy(self, request, pk, *args, **kwargs):
        headers = getHeaders(request)
        try:
            response = requests.delete(
                f'{RESERVATIONS_SERVICE_URL}payments/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
