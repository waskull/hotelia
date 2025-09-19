from datetime import datetime
from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.models import Group, Permission
# from django.contrib.auth import get_user_model

# Django REST Framework
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

# Models
from .models import Reservation, Payment, PaymentMethod

# User = get_user_model()

class ReservationCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    room_id = serializers.IntegerField(read_only=True)

class ReservationSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=False)
    class Meta:
        model = Reservation
        fields = '__all__'
        extra_kwargs = {
            "total_price": {"read_only": True},
        }

    def validate(self, data):
        if data["end_date"] < data["start_date"]:
            raise serializers.ValidationError("La fecha de salida debe ser posterior a la fecha entrada")
        if data["end_date"] < datetime.now().date():
            raise serializers.ValidationError("La fecha de salida debe ser posterior a la fecha actual")
        if data["start_date"] < datetime.now().date():
            raise serializers.ValidationError("La fecha de entrada debe ser posterior a la fecha actual")

        return data

    def create(self, validated_data):
        return Reservation.objects.create(**validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    class Meta:
        model = Payment
        fields = "__all__"

class ReservationPaymentSerializer(serializers.ModelSerializer):
    Reservation = ReservationSerializer(many=False, read_only=True)
    class Meta:
        model = Payment
        fields = "__all__"
