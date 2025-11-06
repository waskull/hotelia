from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.models import Group, Permission
from rest_framework.validators import UniqueTogetherValidator
from PIL import Image
# from django.contrib.auth import get_user_model

# Django REST Framework
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
# Models
from .models import Hotel, Review, Room

# User = get_user_model()


class HotelSerializer(serializers.ModelSerializer):
    # total_rooms = serializers.ReadOnlyField()

    # def get_total_rooms(self, obj):
    #     return Room.objects.filter(hotel=obj).count()

    class Meta:
        model = Hotel
        fields = ('id', 'name', 'city', 'address', 'description',
                  'image', 'services', 'star_rating', 'payment_policy', 'reservation_policy', 'phone','email')

    validators = [
        UniqueTogetherValidator(
            queryset=Hotel.objects.all(),
            fields=['name', 'city'],
            message="El hotel ya existe en la ciudad seleccionada."
        ),
        UniqueValidator(
            queryset=Hotel.objects.all(),
            message="El hotel ya existe."
        )
    ]

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def validate_image(self, value):
        if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError(
                "Solo se permite imagenes con extensiones .png o .jpg o .jpeg.")
        try:
            img = Image.open(value)
            img.verify()
        except Exception:
            raise serializers.ValidationError("Imagen invalida.")
        return value

    def create(self, validated_data):
        Hotel.objects.create(**validated_data)

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"
        extra_kwargs = {
            "user_id": {"read_only": True},
        }

class RoomSerializer(serializers.ModelSerializer):
    hotel_name = serializers.ReadOnlyField(source='hotel.name')
    class Meta:
        model = Room
        fields = "__all__"

    validators = [
            UniqueTogetherValidator(
                queryset=Room.objects.all(),
                fields=['room_number', 'hotel'],
                message="Esta habitación ya existe en el hotel seleccionado. Por favor, elige un número diferente."
            )
        ]
