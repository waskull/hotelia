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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
