import requests
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserLoginSerializer, UserRegisterSerializer, HotelSerializer, RoomSerializer, ReservationSerializer, PaymentSerializer
# Create your views here.
USERS_SERVICE_URL = 'http://localhost:8001/api/'
HOTELS_SERVICE_URL = 'http://localhost:8002/api/'
RESERVATIONS_SERVICE_URL = 'http://localhost:8003/api/'


class UserRegisterView(APIView):
    serializer_class = UserRegisterSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            response = requests.post(
                f'{USERS_SERVICE_URL}auth/', json=request.data)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserLoginView(APIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            response = requests.post(
                f'{USERS_SERVICE_URL}auth/login/', json=serializer.data)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        print("Headers: ",headers)
        try:
            response = requests.get(
                f'{USERS_SERVICE_URL}auth/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserProfileView(APIView):
    #permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        print("Headers: ",headers)
        try:
            response = requests.get(
                f'{USERS_SERVICE_URL}auth/me/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class HotelListView(APIView):
    #permission_classes = [IsAuthenticated]
    serializer_class = HotelSerializer

    def get(self, request, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.get(
                f'{HOTELS_SERVICE_URL}hotels/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def post(self, request, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.post(
                f'{HOTELS_SERVICE_URL}hotels/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class HotelDetailView(APIView):
    #permission_classes = [IsAuthenticated]
    serializer_class = HotelSerializer

    def get(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.get(
                f'{HOTELS_SERVICE_URL}hotels/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def put(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.put(
                f'{HOTELS_SERVICE_URL}hotels/{pk}/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def delete(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.delete(
                f'{HOTELS_SERVICE_URL}hotels/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# room
class RoomListView(APIView):
    #permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializer

    def get(self, request, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.get(
                f'{HOTELS_SERVICE_URL}rooms/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def post(self, request, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.post(
                f'{HOTELS_SERVICE_URL}rooms/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class RoomDetailView(APIView):
    #permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializer

    def get(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.get(
                f'{HOTELS_SERVICE_URL}rooms/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def put(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.put(
                f'{HOTELS_SERVICE_URL}rooms/{pk}/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def delete(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.delete(
                f'{HOTELS_SERVICE_URL}rooms/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ReservationListView(APIView):
    #permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.get(
                f'{RESERVATIONS_SERVICE_URL}reservations/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class CreateReservationView(APIView):
    #permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.post(
                f'{RESERVATIONS_SERVICE_URL}reservations/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ReservationDetailView(APIView):
    #permission_classes = [IsAuthenticated]
    serializer_class = ReservationSerializer

    def get(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.get(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def put(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.put(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def delete(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.delete(
                f'{RESERVATIONS_SERVICE_URL}reservations/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class PaymentListView(APIView):
    #permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get(self, request, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.get(
                f'{HOTELS_SERVICE_URL}payments/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def post(self, request, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.post(
                f'{HOTELS_SERVICE_URL}payments/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class PaymentDetailView(APIView):
    #permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.get(
                f'{RESERVATIONS_SERVICE_URL}payments/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def put(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.put(
                f'{RESERVATIONS_SERVICE_URL}payments/{pk}/', json=request.data, headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def delete(self, request, pk, *args, **kwargs):
        headers = {'Authorization': request.headers.get('Authorization')}
        try:
            response = requests.delete(
                f'{RESERVATIONS_SERVICE_URL}payments/{pk}/', headers=headers)
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
