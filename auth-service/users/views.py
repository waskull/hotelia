# Django REST Framework
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

# Permissions
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

# Serializers
from . import serializers

# Models

User = get_user_model()

class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    User view set.

    Handle login and logout.
    """

    queryset = User.objects.all()
    serializer_class = serializers.UserModelSerializer

    def get_permissions(self):
        """Assign permissions based on action."""
        permissions = [AllowAny]
        if self.action in ["logout"]:
            permissions = [IsAuthenticated]
        return [p() for p in permissions]

    @action(detail=False, methods=["post"])
    def login(self, request):
        """User sign in."""
        serializer = serializers.UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer_data = serializer.save()
        data = {
            "user": self.get_serializer(serializer_data["user"]).data,
            "access_token": serializer_data["access_token"],
            "refresh_token": serializer_data["refresh_token"],
            "message": "Sesión iniciada con exito",
        }
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """User logout to the system"""
        serializer = serializers.UserLogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = {"message": "Te has desconectado del sistema"}
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def my_profile(self, request):
        data = self.get_serializer(request.user).data
        return Response(data, status=status.HTTP_200_OK)
