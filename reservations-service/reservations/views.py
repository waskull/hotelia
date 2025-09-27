from django.db.models import Q, Count, Sum
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
import httpx
import asyncio
from asgiref.sync import async_to_sync
from .models import Reservation, Payment, Status
from .serializers import ReservationCountSerializer, ReservationSerializer, UpdateReservationSerializer, PaymentSerializer, ReservationPaymentSerializer
# from .authentication import UserAuthentication
# Create your views here.

HOTELS_SERVICE_URL = 'http://localhost:8002/api/'
NOTIFICATIONS_SERVICE_URL = 'http://localhost:8004/api/'
GATEWAY_SERVICE_URL = 'http://localhost:8000/'


async def fetch_data(client, url, headers, timeout=10.0):
    try:
        print(url, headers, timeout)
        response = await client.get(url=url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Lanza una excepción para errores HTTP
        return response.json()
    except httpx.HTTPStatusError as exc:
        return {"error": f"Error en la petición: {exc.response.status_code}"}
    except httpx.RequestError as exc:
        return {"error": f"Error en petición: {exc}", "url": exc.request.url}
    except Exception as exc:
        return {"error": f"Error desconocido: {exc}"}


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ReservationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

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

    @action(detail=False, methods=["get"])
    def top(self, request):
        try:
            user_id = request.user.id
            top_popular_rooms = Reservation.objects.filter(user_id=user_id).values(
                'room_id').annotate(count=Count('room_id')).order_by('-count')[:5]
            serializer = ReservationCountSerializer(
                top_popular_rooms, many=True)
            return Response(serializer.data)
        except Reservation.DoesNotExist:
            return Response({"error": "No se encontro habitaciones para dicho usuario", })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"])
    def user(self, request):
        try:
            reservations = Reservation.objects.filter(user_id=request.user.id)
            serializer = ReservationSerializer(reservations, many=True)
            return Response(serializer.data)
        except Reservation.DoesNotExist:
            return Response({"error": "No se encontro reservaciones para dicho usuario", })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["get"])
    def payments(self, request, pk=None):
        if pk is None:
            return Response({"error": "La id del hotel es requerida"}, status=400)
        try:
            payments = Payment.objects.filter(reservation_id=pk)
            serializer = ReservationPaymentSerializer(payments, many=True)
            return Response(serializer.data)
        except Payment.DoesNotExist:
            return Response({"error": "No se encontro pago para dicho hotel", })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = request.data.get("user_id")
        is_cliente = "cliente" in request.user.groups
        email: str = ""

        if user_id and is_cliente:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "No tienes permiso para crear una reserva a otro usuario."})

        if not user_id:
            serializer.validated_data["user_id"] = request.user.id
            email = request.user.email

        if user_id:
            try:
                response = httpx.get(
                    f'{GATEWAY_SERVICE_URL}users/{serializer.validated_data["user_id"]}/', headers={'Authorization': request.headers.get(
                        'Authorization')})
                response.raise_for_status()
                email = response.json()['email']
                print(email)
            except httpx.RequestError as e:
                return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    return Response({"error": "El usuario no existe."}, status=status.HTTP_404_NOT_FOUND)
                return Response({"error": f"Error en la petición: {exc.response.status_code}"})

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]
        room_id = serializer.validated_data["room_id"]

        cost_night = 0.0
        try:
            response = httpx.get(
                f'{HOTELS_SERVICE_URL}rooms/{room_id}/', headers={'Authorization': request.headers.get(
                    'Authorization')})
            response.raise_for_status()
            cost_night = response.json()['price_per_night']
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return Response({"error": "La habitación no existe."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": f"Error en la petición: {exc.response.status_code}"})

        days = int((end_date - start_date).days)
        total: float = days * float(cost_night)
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
        try:
            json = {
                "subject": "Reserva realizada",
                "body": f"Hola {request.user.first_name}, tu reserva para la habitación {room_id} del {start_date} al {end_date} ha sido realizada.",
                "destinations": [email]
            }
            if (email):
                response = httpx.get(
                    f'{NOTIFICATIONS_SERVICE_URL}api/email/', json=json, headers={'X-Notification-Gateway-Token': settings.NOTIFICATION_GATEWAY_TOKEN})
                response.raise_for_status()
                print(response.json)
        except httpx.RequestError as e:
            print("No se pudo enviar el correo")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(
            user_id=self.request.user.id,
            room_id=serializer.validated_data["room_id"],
            total_price=serializer.validated_data["total_price"],
            start_date=serializer.validated_data["start_date"],
            end_date=serializer.validated_data["end_date"]
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None, *args, **kwargs):
        reservation = self.get_object()
        serializer = self.get_serializer(
            reservation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        is_cliente = "cliente" in request.user.groups
        if serializer.validated_data["user_id"] != request.user.id and is_cliente:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "No tienes permiso para cancelar esta reserva."})

        if reservation.status == Status.CANCELLED:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "Esta reserva ya fue cancelada"})

        elif reservation.status != Status.PENDING:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "No puedes cancelar esta reserva."})

        serializer.save(
            user_id=serializer.validated_data["user_id"],
            status=Status.CANCELLED,
            room_id=serializer.validated_data["room_id"],
            total_price=serializer.validated_data["total_price"],
            start_date=serializer.validated_data["start_date"],
            end_date=serializer.validated_data["end_date"]
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk, *args, **kwargs):
        reservation = self.get_object()
        serializer = UpdateReservationSerializer(
            reservation, data=request.data)
        serializer.is_valid(raise_exception=True)

        if reservation.status != Status.PENDING:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "Ya no puedes actualizar esta reserva."})

        is_cliente = "cliente" in request.user.groups
        if reservation.user_id != request.user.id and is_cliente:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "No tienes permiso para actualizar esta reserva."})

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]
        room_id = serializer.validated_data["room_id"]

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

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk, *args, **kwargs):
        reservation = Reservation.objects.get(pk=pk)
        print(reservation)
        # return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "ASD."})
        is_cliente = "cliente" in request.user.groups
        if reservation.user_id != request.user.id and is_cliente:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "No tienes permiso para actualizar esta reserva."})

        if reservation.status == Status.CANCELLED:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "Esta reserva ya fue cancelada"})

        if reservation.status == Status.COMPLETED:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": f"Esta reserva ya fue completada."})

        new_status = ""
        if reservation.status == Status.PENDING:
            new_status = Status.CONFIRMED
        elif reservation.status == Status.CONFIRMED:
            new_status = Status.PREPARING
        elif reservation.status == Status.PREPARING:
            new_status = Status.OCUPPIED
        else:  # Status.OCUPPIED
            new_status = Status.COMPLETED

        reservation.status = new_status
        reservation.save()
        return Response({"message": "Reserva actualizada"}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        reservation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
