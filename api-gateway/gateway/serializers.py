from rest_framework import serializers
from datetime import time, datetime
from django.utils import timezone

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class UserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    dni = serializers.CharField()
    last_login = serializers.DateTimeField(required=False, allow_null=True)
    groups = serializers.ListField()
    is_active = serializers.BooleanField()
    phone = serializers.CharField()
    id = serializers.IntegerField()


class UpdateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    dni = serializers.CharField()
    phone = serializers.CharField()


class UpdateUserPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    password_confirmation = serializers.CharField()


class UserRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    password_confirmation = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    dni = serializers.CharField()
    role = serializers.CharField()
    phone = serializers.CharField()

class UserLogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

class UserProfileResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField()
    dni = serializers.CharField(max_length=15)
    phone = serializers.CharField(max_length=20, required=False)
    is_superuser = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    is_active = serializers.BooleanField()
    last_login = serializers.DateTimeField(allow_null=True)
    # Usamos CharField para cada elemento, asumiendo que los grupos son cadenas de texto
    groups = serializers.ListField(
        child=serializers.CharField(max_length=100)
    )

    class Meta:
        extra_kwargs = {
            '*': {'read_only': True}
        }


class HotelSerializer(serializers.Serializer):
    name = serializers.CharField()
    city = serializers.CharField()
    address = serializers.CharField()
    description = serializers.CharField()
    payment_policy = serializers.CharField()
    reservation_policy = serializers.CharField()
    image = serializers.ImageField()
    phone = serializers.CharField()
    email = serializers.EmailField(required=False)
    services = serializers.CharField()
    star_rating = serializers.IntegerField()


class ReviewSerializer(serializers.Serializer):
    rating = serializers.IntegerField()
    comment = serializers.CharField(required=False)
    hotel = serializers.IntegerField()

    def validate(self, data):
        if data["rating"] < 1 or data["rating"] > 5:
            raise serializers.ValidationError(
                "La calificacion debe estar entre 1 y 5")
        return data


class RoomSerializer(serializers.Serializer):
    capacity = serializers.IntegerField()
    room_type = serializers.CharField()
    room_number = serializers.IntegerField()
    price_per_night = serializers.DecimalField(max_digits=10, decimal_places=2)
    hotel = serializers.IntegerField()
    hotel_name = serializers.CharField(required=False)


class RoomResponseSerializer(RoomSerializer):
    status = serializers.CharField()
    id = serializers.IntegerField(required=False)


class ReservationSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    user_id = serializers.IntegerField(required=False)
    start_date = serializers.DateTimeField(input_formats=['%d/%m/%Y %I:%M %p', 'iso-8601'])
    end_date = serializers.DateTimeField(input_formats=['%d/%m/%Y %I:%M %p', 'iso-8601'])
    status = serializers.CharField()


class CreateReservationSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    start_date = serializers.DateTimeField(input_formats=['%d/%m/%Y %I:%M %p', 'iso-8601'])
    end_date = serializers.DateTimeField(input_formats=['%d/%m/%Y %I:%M %p', 'iso-8601'])
    user_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError(
                "La fecha de salida debe ser posterior a la fecha entrada")
        if data["end_date"] < timezone.now():
            raise serializers.ValidationError(
                "La fecha de salida debe ser posterior a la fecha actual")
        if data["start_date"].date() < timezone.now().date():
            raise serializers.ValidationError(
                "La fecha de entrada debe ser posterior a la fecha actual")

        min_start_time = time(11, 00)    # 10:00 AM (10:00 AM)
        max_start_time = time(22, 15)
        start_time = data["start_date"].time()

        end_time = data["end_date"].time()
        min_end_time = time(7, 45)
        max_end_time = time(10, 15)  # 10:15 AM

        # Comprobar si la hora está fuera del rango
        if not (min_start_time <= start_time <= max_start_time):
            raise serializers.ValidationError(
                "La hora de entrada debe de estar entre las 11:00 AM y las 10:15 PM."
            )

        if not (min_end_time <= end_time <= max_end_time):
            raise serializers.ValidationError(
                "La hora de salida debe de estar entre las 7:45 AM y las 10:15 AM."
            )
        return data


class UpdateReservationSerializer(CreateReservationSerializer):
    user_id = serializers.IntegerField(required=True, allow_null=False)


class ExtendReservationSerializer(serializers.Serializer):
    end_date = serializers.DateTimeField(
        input_formats=['%d/%m/%Y %I:%M %p', 'iso-8601'])

    def validate_end_date(self, value: datetime):
        date = value.date()
        if date < timezone.now().date():
            raise serializers.ValidationError(
                "La nueva fecha de salida debe ser posterior a la fecha actual"
            )
        end_time = value.time()
        min_end_time = time(7, 45)
        max_end_time = time(10, 15)  # 10:15 AM

        if not (min_end_time <= end_time <= max_end_time):
            raise serializers.ValidationError(
                "La hora de salida debe de estar entre las 7:45 AM y las 10:15 AM."
            )

        return value


class PaymentSerializer(serializers.Serializer):
    reservation = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField()
    ref_code = serializers.CharField()
    payment_date = serializers.DateField()


class ChatResponseSerializer(serializers.Serializer):
    user_id = serializers.CharField(
        help_text="ID del usuario que hizo la consulta.")
    query = serializers.CharField(
        help_text="Pregunta original enviada por el usuario.")
    response = serializers.CharField(
        help_text="Respuesta generada por el modelo LLaMA u Ollama.")


class ChatRequestSerializer(serializers.Serializer):
    query = serializers.CharField(
        required=True, help_text="Texto o pregunta del usuario para el asistente de reservas.")