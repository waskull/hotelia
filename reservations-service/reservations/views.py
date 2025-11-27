from django.db.models import Q, Count
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.conf import settings
from datetime import datetime
from dateutil import parser
import httpx
# from asgiref.sync import async_to_sync
from .models import Reservation, Payment, Status, PaymentMethod
from .serializers import ReservationCountSerializer, ExtendReservationSerializer, ReservationSerializer, UpdateReservationSerializer, PaymentSerializer, ReservationPaymentSerializer
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
        msg = f"Hola {fullname}, tu reserva para la habitación #{room_id} del {format_date(start_date)} al {format_date(end_date)}"
        subject = "Reserva realizada"
        if status == Status.OCUPPIED:
            msg = f"{msg} ha sido aprobada y esta esperando por ti."
            subject = "Reserva Confirmada"
        else:
            msg = f"{msg} ha sido realizada y una vez confirmado el pago se le notificara con un correo."
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


def format_date(timedatestamp: datetime):
    return parser.isoparse(str(timedatestamp)).strftime("%d/%m/%Y %I:%M %p")


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
                # La nueva fecha de fin debe ser posterior a la fecha de inicio de la reserva existente.
                start_date__lt=end_date,
                # La nueva fecha de inicio debe ser anterior a la fecha de fin de la reserva existente.
                end_date__gt=start_date,
            ).values_list("room_id", flat=True)

            # Excluir esas habitaciones del queryset principal
            queryset = queryset.exclude(room_id__in=reserved_rooms)
        if status:
            queryset = queryset.filter(status__icontains=status)
        return queryset

    @action(detail=False, methods=["get"])
    def top(self, request):
        try:
            is_authenticated = request.user.is_authenticated
            global_top = request.query_params.get("global", "false")
            if global_top == "true" or not is_authenticated:
                top_popular_rooms = Reservation.objects.filter(status__in=[Status.COMPLETED, Status.PREPARING, Status.OCUPPIED, Status.CONFIRMED]).values(
                    'room_id').annotate(count=Count('room_id')).order_by('-count')[:5]
            else:
                user_id = request.user.id
                top_popular_rooms = Reservation.objects.filter(user_id=user_id, status__in=[Status.COMPLETED, Status.PREPARING, Status.OCUPPIED, Status.CONFIRMED]).values(
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
        is_authenticated = request.user.is_authenticated
        try:
            me = request.query_params.get("me", "false")
            rows = int(self.request.query_params.get("rows") or 5)
            if rows < 0:
                rows = 5
            if rows > 10:
                rows = 10
            top_popular_rooms = []
            if me == "false" or not is_authenticated:
                top_popular_rooms = Reservation.objects.filter(status__in=[Status.COMPLETED, Status.PREPARING, Status.OCUPPIED, Status.CONFIRMED]).values(
                    'room_id').annotate(count=Count('room_id')).order_by('-count')[:rows]
            else:
                user_id = request.user.id
                top_popular_rooms = Reservation.objects.filter(user_id=user_id, status__in=[Status.COMPLETED, Status.PREPARING, Status.OCUPPIED, Status.CONFIRMED]).values(
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
                print(email, fullname)
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

        days = int((end_date.date() - start_date.date()).days)
        total: float = days * float(cost_night)
        serializer.validated_data["total_price"] = total
        overlapping = Reservation.objects.filter(
            room_id=room_id,
            start_date__lt=end_date,
            end_date__gt=start_date,
        ).filter(
            status__in=[Status.PENDING, Status.CONFIRMED,
                        Status.PREPARING, Status.OCUPPIED]
        )

        if overlapping.exists():
            return Response(
                {"error": "La habitación ya está reservada en este rango de fechas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si está libre, crear la reserva
        self.perform_create(serializer)
        send_email(user_id=user_id, email=email, request=request, room_id=room_id,
                   start_date=start_date, end_date=end_date, status=Status.PENDING, fullname=fullname)
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
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        is_cliente = "cliente" in request.user.groups
        if reservation.user_id != request.user.id and is_cliente:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "No tienes permiso para cancelar esta reserva."})

        if reservation.status == Status.CANCELLED:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "Esta reserva ya fue cancelada"})

        elif reservation.status != Status.PENDING:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "No puedes cancelar esta reserva."})
        reservation.status = Status.CANCELLED
        reservation.save()
        full_serializer = ReservationSerializer(reservation)
        return Response(full_serializer.data, status=status.HTTP_200_OK)

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
            room_id=room_id,
            start_date__lt=end_date,
            end_date__gt=start_date,
        ).exclude(
            pk=reservation.pk
        ).filter(
            status__in=[Status.PENDING, Status.CONFIRMED,
                        Status.PREPARING, Status.OCUPPIED]
        )

        if overlapping.exists():
            return Response(
                {"error": "La habitación ya está reservada por otra persona en este rango de fechas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Recálculo del precio total si las fechas o la habitación cambiaron
        if start_date != reservation.start_date or end_date != reservation.end_date or room_id != reservation.room_id:
            cost_night = 0.0
            try:
                response = httpx.get(
                    f'{HOTELS_SERVICE_URL}rooms/{room_id}/', headers={'Authorization': request.headers.get('Authorization')})
                response.raise_for_status()
                result = response.json()
                cost_night = result['price_per_night']
            except httpx.RequestError as e:
                return Response({'error': f'Error al contactar el servicio de hoteles: {str(e)}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            except httpx.HTTPStatusError as exc:
                return Response({"error": f"La habitación con ID {room_id} no existe o no está disponible."}, status=status.HTTP_404_NOT_FOUND)

            days = int((end_date.date() - start_date.date()).days)
            total: float = days * float(cost_night)
            serializer.validated_data["total_price"] = total

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk, *args, **kwargs):
        reservation = Reservation.objects.get(pk=pk)
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

    @action(detail=True, methods=["post"])
    def extend_reservation(self, request, pk=None):
        reservation = self.get_object()
        print(reservation.start_date, reservation.end_date)
        seri = ExtendReservationSerializer(data=request.data)
        seri.is_valid(raise_exception=True)
        end = Reservation.objects.get(pk=pk).end_date
        new_end_date_str = request.data.get("end_date")
        if not new_end_date_str:
            return Response({"error": "La nueva fecha de fin ('end_date') es requerida."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_end_date = datetime.fromisoformat(new_end_date_str)
            new_end_date = new_end_date
        except ValueError:
            return Response({"error": "Formato de fecha de fin inválido. Use formato YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        if reservation.status == Status.CANCELLED or reservation.status == Status.COMPLETED:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "Esta reserva ya no puede extenderse."})

        is_cliente = "cliente" in request.user.groups
        if reservation.user_id != request.user.id and is_cliente:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": "No tienes permiso para actualizar esta reserva."})

        if new_end_date <= end:
            return Response(
                {"error": "La nueva fecha de fin debe ser estrictamente posterior a la fecha de fin actual."},
                status=status.HTTP_400_BAD_REQUEST
            )
        current_start_date = reservation.start_date
        room_id = reservation.room_id

        overlapping = Reservation.objects.filter(
            room_id=room_id,
            start_date__lt=new_end_date,
            end_date__gt=current_start_date,
        ).exclude(
            pk=reservation.pk
        ).filter(
            status__in=[Status.PENDING, Status.CONFIRMED,
                        Status.PREPARING, Status.OCUPPIED]
        )

        if overlapping.exists():
            return Response(
                {"error": "No es posible extender la reserva. La habitación ya ha sido reservada por otra persona en el nuevo rango de fechas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Recálculo del precio total
        try:
            response = httpx.get(
                f'{HOTELS_SERVICE_URL}rooms/{room_id}/', headers={'Authorization': request.headers.get('Authorization')})
            response.raise_for_status()
            result = response.json()
            cost_night = float(result['price_per_night'])
        except httpx.RequestError:
            return Response({'error': 'Error al contactar el servicio de hoteles para obtener el precio.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except httpx.HTTPStatusError:
            return Response({"error": "No se pudo obtener el precio de la habitación."}, status=status.HTTP_404_NOT_FOUND)
        days = int((new_end_date.date() - current_start_date.date()).days)
        new_total_price = days * cost_night
        print(days)
        reservation.end_date = new_end_date
        reservation.total_price = new_total_price
        reservation.save()
        formatted_date = format_date(new_end_date)
        return Response({"message": f"Reserva actualizada, la nueva fecha de salida es: {formatted_date}, y el total a pagar es: {new_total_price}"}, status=status.HTTP_200_OK)
