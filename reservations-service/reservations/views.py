from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from datetime import datetime
import requests
from .models import Reservation, Payment, StateStatus
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
        user_id = request.data.get("user_id")
        is_admin = "admin" in request.user.groups
        is_staff = "recepcionista" in request.user.groups

        if user_id and not (is_admin or is_staff):
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "No tienes permiso para crear una reserva a otro usuario."})

        if not user_id:
            serializer.validated_data["user_id"] = request.user.id

        # return Response(status=status.HTTP_201_CREATED, data={"message": "Reserva creada con exito"})

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]
        room_id = serializer.validated_data["room_id"]

        cost_night = 0.0

        try:
            response = requests.get(
                f'{HOTELS_SERVICE_URL}rooms/{room_id}/', headers={'Authorization': request.headers.get(
                    'Authorization')})
            response.raise_for_status()
            if response.status_code == 404:
                return Response({"error": "La habitación no existe."}, status=status.HTTP_404_NOT_FOUND)
            cost_night = response.json()['price_per_night']
        except requests.exceptions.RequestException as e:
            if e.response.status_code == 404:
                return Response({"error": "La habitación no existe."}, status=status.HTTP_404_NOT_FOUND)
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if end_date < start_date:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "La fecha de salida debe ser posterior a la fecha entrada"})
        elif end_date < datetime.now().date():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "La fecha de salida debe ser posterior a la fecha actual"})
        elif start_date < datetime.now().date():
            return Response(status=status.HTTP_400_BAD_REQUEST, message="La fecha de entrada debe ser posterior a la fecha actual")
        
        days = int((end_date - start_date).days)
        total:float = days * float(cost_night)
        serializer.validated_data["total_price"] = total
        print(serializer.validated_data)

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

    def perform_create(self, serializer):
        serializer.save(
            user_id=self.request.user.id,
            room_id=serializer.validated_data["room_id"],
            total_price=serializer.validated_data["total_price"],
            start_date=serializer.validated_data["start_date"],
            end_date=serializer.validated_data["end_date"]
        )

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        reservation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
