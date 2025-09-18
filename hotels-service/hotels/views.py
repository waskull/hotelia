from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from .authentication import UserAuthentication
from .models import Hotel, Room
from .serializers import HotelSerializer, RoomSerializer
# Create your views here.


class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    #authentication_classes = [UserAuthentication]
    #permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FileUploadParser,)

    def get_queryset(self):
        #print("user: ", self.request.user.id)
        queryset = super().get_queryset()
        city = self.request.query_params.get("city")
        if city:
            queryset = queryset.filter(city__icontains=city)
        return queryset
    
    def create(self, request, *args, **kwargs):
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            already_exists = Hotel.objects.filter(Q(name=serializer.data['name']) & Q(city=serializer.data['city'])).exists()
            if already_exists:
                return Response({"error": f"El hotel {serializer.data['name']} ya existe en la ciudad de {serializer.data['city']}"}, status=status.HTTP_400_BAD_REQUEST)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    def perform_create(self, serializer):
        Hotel.objects.create(**serializer.validated_data)

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    #permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        hotel_id = self.request.query_params.get("hotel_id")
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        return queryset