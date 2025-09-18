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
    class Meta:
        model = Reservation
        fields = "__all__"

    def create(self, validated_data):
        return Reservation.objects.create(**validated_data)

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"