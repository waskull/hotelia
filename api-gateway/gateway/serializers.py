from rest_framework import serializers

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
            raise serializers.ValidationError("La calificacion debe estar entre 1 y 5")
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
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    status = serializers.CharField()
    #total_price = serializers.DecimalField(max_digits=10, decimal_places=2)

class PaymentSerializer(serializers.Serializer):
    reservation = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField()
    ref_code = serializers.CharField()
    payment_date = serializers.DateField()