from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.models import Group, Permission
from PIL import Image
# from django.contrib.auth import get_user_model

# Django REST Framework
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
# Models
from .models import Hotel, Room

# User = get_user_model()


class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = ('id', 'name', 'city', 'address', 'description', 'image')

    def validate_image(self, value):
            if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise serializers.ValidationError("Solo se permite imagenes con extensiones .png o .jpg o .jpeg.")
            try:
                img = Image.open(value)
                img.verify() # Verify if it's a valid image
            except Exception:
                raise serializers.ValidationError("Imagen invalida.")
            return value
    
    def create(self, validated_data):
        return Hotel.objects.create(**validated_data)

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"