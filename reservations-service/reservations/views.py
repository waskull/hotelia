from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from datetime import datetime

from .models import Reservation, Payment
from .serializers import ReservationSerializer, PaymentSerializer
# Create your views here.

HOTELS_SERVICE_URL = 'http://localhost:8002/api/'


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        city = self.request.query_params.get("city")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if city:
            queryset = queryset.filter(city__icontains=city)

        if start_date and end_date:
            # Buscar habitaciones que ya tienen reservas en ese rango
            reserved_rooms = Reservation.objects.filter(
                Q(start_date__range=(start_date, end_date)) |
                Q(end_date__range=(start_date, end_date))
            ).values_list("room_id", flat=True)

            # Excluir esas habitaciones del queryset principal
            queryset = queryset.exclude(room_id__in=reserved_rooms)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["start_date"]
        room_id = serializer.validated_data["room_id"]

        if end_date < start_date:
            return Response(status=status.HTTP_400_BAD_REQUEST, message="La fecha de salida debe ser posterior a la fecha de entrada")
        elif end_date < datetime.now().date():
            return Response(status=status.HTTP_400_BAD_REQUEST, message="La fecha de salida debe ser posterior a la fecha actual")
        elif start_date < datetime.now().date():
            return Response(status=status.HTTP_400_BAD_REQUEST, message="La fecha de entrada debe ser posterior a la fecha actual")

        overlapping = Reservation.objects.filter(
            room_id=room_id
        ).filter(
            Q(start_date__range=(start_date, end_date)) |
            Q(end_date__range=(start_date, end_date)) |
            # Caso: reserva que cubre todo el rango
            Q(start_date__lte=start_date, end_date__gte=end_date)
        )

        if overlapping.exists():
            return Response(
                {"error": "La habitación ya está reservada en este rango de fechas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si está libre, crear la reserva
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        """ room_from_request = serializer.validated_data["room_id"]
        room_is_available = not Reservation.objects.get(
            room_id=room_from_request).exists()

        if room_is_available:
            # Terminar Luego hacer peticion a microservicio de hotels y traer informacion de la habitación del hotel
            headers = {'Authorization': request.headers.get(
                'Authorization')}
            response = requests.get(
                f'{HOTELS_SERVICE_URL}rooms/{room_from_request}/', headers=headers)
            res = response.json()
            total_days = (end_date - start_date).days
            total_to_pay = total_days * room.price_per_night
            Reservation.objects.create(user_id=request.user.id, room_id=room.id,
                                       start_date=start_date, end_date=end_date, total_price=total_to_pay)

            return Response(status=status.HTTP_201_CREATED, message="La Reserva ha sido creada")

        return Response(status=status.HTTP_400_BAD_REQUEST, message="Habitación no disponible en las fechas seleccionadas") """

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        reservation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
