from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.models import Group, Permission
# from django.contrib.auth import get_user_model

# Django REST Framework
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
# Models
from .models import Hotel, Room

# User = get_user_model()


class HotelSerializer(serializers.Serializer):
    class Meta:
        model = Hotel
        fields = "__all__"

class RoomSerializer(serializers.Serializer):
    class Meta:
        model = Room
        fields = "__all__"