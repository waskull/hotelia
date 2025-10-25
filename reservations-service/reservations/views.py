from django.db.models import Q, Count
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.conf import settings
import httpx
# from asgiref.sync import async_to_sync
from .models import Reservation, Payment, Status, PaymentMethod
from .serializers import ReservationCountSerializer, ReservationSerializer, UpdateReservationSerializer, PaymentSerializer, ReservationPaymentSerializer
# from .authentication import UserAuthentication
# Create your views here.

HOTELS_SERVICE_URL = settings.HOTELS_SERVICE_URL
NOTIFICATIONS_SERVICE_URL = settings.NOTIFICATIONS_SERVICE_URL
GATEWAY_SERVICE_URL = settings.GATEWAY_SERVICE_URL
AUTH_SERVICE_URL = settings.AUTH_SERVICE_URL


def send_email(user_id, request, room_id, start_date, end_date, status, fullname=None, email=None):
    try:
        user = {}
        if not fullname and not email:
            user = httpx.get(f'{AUTH_SERVICE_URL}auth/{user_id}/', headers={
            'Authorization': request.headers.get('Authorization')}).json()
            fullname = f"{user['first_name']} {user['last_name']}"
            email = user['email']
        msg = f"Hola {fullname}, tu reserva para la habitación #{room_id} del {start_date} al {end_date} 11:00am"
        subject = "Reserva realizada"
        if status == Status.COMPLETED:
            msg = f"{msg} ha sido realizada y esta esperando por ti."
            subject = "Reserva Confirmada"
        else:
            msg = f"{msg} ha sido realizada y esta en espera por confirmación de la administración."
        json = {
            "subject": subject,
            "body": msg,
            "destinations": [email]
        }
        if email:
            response = httpx.post(
                f'{NOTIFICATIONS_SERVICE_URL}email/', json=json, headers={'X-Notification-Gateway-Token': settings.NOTIFICATION_TOKEN})
            response.raise_for_status()
            print(response.json())
    except httpx.RequestError as e:
        print("No se pudo enviar el correo")


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        top_count_method = Payment.objects.values('payment_method').annotate(
            count=Count('payment_method')).order_by('-count')[:5]
        top_users = Reservation.objects.filter(status=Status.COMPLETED).values(
            'user_id').annotate(count=Count('user_id')).order_by('-count')
        return Response({"top_method": top_count_method, "top_users": top_users}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):

        if len(request.data.get("ref_code")) > 0 and request.data.get("payment_method") in [PaymentMethod.CASH, PaymentMethod.DEBIT_CARD, PaymentMethod.CREDIT_CARD]:
            request.data.pop("ref_code")
        print(request.data)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        Payment.objects.create(**serializer.validated_data)
        return Response({"message": "Pago realizado con exito"}, status=status.HTTP_201_CREATED)


class ReservationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        city = self.request.query_params.get("city")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        status = self.request.query_params.get("status")
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
        if status:
            queryset = queryset.filter(status__icontains=status)
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
    def top_hotels(self, request):
        try:
            me = request.query_params.get("me")
            rows = int(self.request.query_params.get("rows") or 5)
            if rows < 0:
                rows = 5
            if rows > 10:
                rows = 10
            top_popular_rooms = []
            if me == "true":
                print("user: ", request.user.id)
                user_id = request.user.id
                top_popular_rooms = Reservation.objects.filter(user_id=user_id).values(
                    'room_id').annotate(count=Count('room_id')).order_by('-count')[:rows]
            else:
                top_popular_rooms = Reservation.objects.all().values(
                    'room_id').annotate(count=Count('room_id')).order_by('-count')[:rows]
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
        email = ""
        fullname = ""
        if user_id and is_cliente:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "No tienes permiso para crear una reserva a otro usuario."})

        if not user_id:
            serializer.validated_data["user_id"] = request.user.id
            email = request.user.email

        if user_id:
            try:
                response = httpx.get(
                    f'{AUTH_SERVICE_URL}auth/{serializer.validated_data["user_id"]}/', headers={'Authorization': request.headers.get(
                        'Authorization')})
                response.raise_for_status()
                json = response.json()
                email = json.get("email")
                fullname = f"{json['first_name']} {json['last_name']}"
                print(email,fullname)
            except httpx.RequestError as e:
                return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    return Response({"error": "El usuario no existe."}, status=status.HTTP_404_NOT_FOUND)
                return Response({"error": f"Error en la petición: {exc.response.status_code}"})

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]
        room_id = serializer.validated_data["room_id"]
        result = {}
        cost_night = 0.0
        try:
            response = httpx.get(
                f'{HOTELS_SERVICE_URL}rooms/{room_id}/', headers={'Authorization': request.headers.get(
                    'Authorization')})
            response.raise_for_status()
            result = response.json()
            if result["status"] != "available":
                return Response({"error": "La habitación no esta disponible."}, status=status.HTTP_400_BAD_REQUEST)
            cost_night = result['price_per_night']
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
        ).filter(
            status__in=[Status.PENDING, Status.CONFIRMED, Status.PREPARING, Status.OCUPPIED]
        )

        if overlapping.exists():
            return Response(
                {"error": "La habitación ya está reservada en este rango de fechas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si está libre, crear la reserva
        self.perform_create(serializer)
        send_email(user_id=user_id, email=email, request=request, room_id=room_id, start_date=start_date, end_date=end_date, status=Status.PENDING, fullname=fullname)
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
        ).filter(
            status__in=[Status.PENDING]
        )
        if overlapping.exists():
            return Response(
                {"error": "Una o la habitación ya está reservada en este rango de fechas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk, *args, **kwargs):
        reservation = Reservation.objects.get(pk=pk)
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
        if new_status == Status.OCUPPIED:
            user_id = reservation.user_id
            room_id = reservation.room_id
            start_date = reservation.start_date
            end_date = reservation.end_date
            send_email(user_id, request, room_id,
                       start_date, end_date, new_status)
        return Response({"message": "Reserva actualizada"}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        reservation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
