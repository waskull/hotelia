from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.models import Group, Permission
# from django.contrib.auth import get_user_model

# Django REST Framework
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

# Models
from .models import Reservation, Payment

# User = get_user_model()


class ReservationSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=False)

    class Meta:
        model = Reservation
        fields = '__all__'
        extra_kwargs = {
            "total_price": {"read_only": True},
        }

    def create(self, validated_data):
        return Reservation.objects.create(**validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
