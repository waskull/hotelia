from rest_framework import serializers

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

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

class HotelSerializer(serializers.Serializer):
    name = serializers.CharField()
    city = serializers.CharField()
    address = serializers.CharField()
    description = serializers.CharField()
    image = serializers.ImageField()

class RoomSerializer(serializers.Serializer):
    name = serializers.CharField()
    capacity = serializers.IntegerField()
    room_type = serializers.CharField()
    room_number = serializers.IntegerField()
    price_per_night = serializers.DecimalField(max_digits=10, decimal_places=2)
    hotel = serializers.IntegerField()

class ReservationSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    user_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    status = serializers.CharField()
    #total_price = serializers.DecimalField(max_digits=10, decimal_places=2)

class PaymentSerializer(serializers.Serializer):
    reservation = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField()
    payment_date = serializers.DateField()