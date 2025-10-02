# Django REST Framework
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch
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

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.UserCreateSerializer
        return self.serializer_class

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
            "id": serializer_data["user"].id,
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
        
    @action(detail=True, methods=["post"])
    def password(self, request, pk=None):
        serializer = serializers.UserPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Contraseña cambiada con éxito"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def permissions(self, request, pk=None):
        if pk is None:
            return Response({"error": "La id del usuario es requerida"}, status=400)
        try:
            user = User.objects.prefetch_related(
                Prefetch('groups'),
                Prefetch('user_permissions')
            ).get(id=pk)

            # Puedes retornar los permisos y grupos como una lista de strings
            user_permissions = list(user.get_all_permissions())
            user_groups = list(user.groups.values_list('name', flat=True))

            return Response({
                'permissions': user_permissions,
                'groups': user_groups,
            })
        except User.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

    @action(detail=False, methods=["get"])
    def me(self, request):
        data = self.get_serializer(request.user).data
        return Response(data, status=status.HTTP_200_OK)
