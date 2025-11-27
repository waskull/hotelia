from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.conf import settings
# Django REST Framework
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.validators import UniqueValidator

# JWT
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed, TokenError

import httpx
# Models

User = get_user_model()

NOTIFICATIONS_SERVICE_URL = settings.NOTIFICATIONS_SERVICE_URL


class GroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["name"]


class UserModelSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    password_confirmation = serializers.CharField(
        min_length=4, max_length=64, write_only=True
    )

    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            "password": {"write_only": True},
            "is_active": {"read_only": True},
            "is_superuser": {"read_only": True},
            "is_staff": {"read_only": True},
            "date_joined": {"write_only": True},
            "user_permissions": {"write_only": True},
        }

    def get_groups(self, obj):
        try:
            serializer = GroupModelSerializer(obj.groups.all(), many=True)
            group = serializer.data
            grps = [x["name"] for x in group]
            return grps
        except Exception:
            return "none"

    def validate(self, data):
        passwd = data["password"]
        passwd_conf = data.pop("password_confirmation")
        if passwd != passwd_conf:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        password_validation.validate_password(passwd)
        data["password"] = make_password(passwd)
        self.context["group"] = data.pop("role", "admin")
        return data

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        group, created = Group.objects.get_or_create(
            name=self.context["group"])
        user.groups.add(group)
        return user


class UserPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=4, max_length=64, write_only=True)
    password_confirmation = serializers.CharField(
        min_length=4, max_length=64, write_only=True)

    def validate(self, data):
        passwd = data["password"]
        passwd_conf = data.pop("password_confirmation")
        if passwd != passwd_conf:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        password_validation.validate_password(passwd)
        data["password"] = make_password(passwd)
        return data


class UserCreateSerializer(UserModelSerializer):

    password_confirmation = serializers.CharField(
        min_length=4, max_length=64, write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "password_confirmation",
            "first_name",
            "last_name",
            "dni",
            "phone",
        )
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, data):
        passwd = data["password"]
        passwd_conf = data.pop("password_confirmation")
        if passwd != passwd_conf:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        password_validation.validate_password(passwd)
        data["password"] = make_password(passwd)
        data["is_active"] = True
        # self.context["group"] = data.pop("role", "cliente")
        return data

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        cliente_group = Group.objects.get_or_create(name='cliente')
        # group, created = Group.objects.get_or_create(name=self.context["group"])
        user.groups.add(cliente_group[0])
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(min_length=6, max_length=30)
    password = serializers.CharField(min_length=4, max_length=20)

    def validate(self, data):
        """Check credentials."""
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise AuthenticationFailed("Credenciales incorrectas")
        self.context["user"] = user
        return data

    def create(self, data):
        user: User = self.context["user"]
        token = RefreshToken.for_user(user)
        refresh_token = str(token)
        access_token = str(token.access_token)
        return {
            "user": user,
            "refresh_token": refresh_token,
            "access_token": access_token,
        }


class UserLogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, data):
        return data

    def save(self, **kwargs):
        try:
            RefreshToken(self.data["refresh_token"]).blacklist()
        except TokenError:
            raise serializers.ValidationError(
                {"error": True, "message": "Token invalido"}
            )
