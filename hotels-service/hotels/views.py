from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from datetime import datetime

from .models import Hotel, Room
from .serializers import HotelSerializer, RoomSerializer
# Create your views here.


class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    #authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        print("user: ", self.request.user.id)
        queryset = super().get_queryset()
        city = self.request.query_params.get("city")
        if city:
            queryset = queryset.filter(city__icontains=city)
        return queryset

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
