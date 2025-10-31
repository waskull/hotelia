import httpx
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from .authentication import UserAuthentication
from rest_framework.decorators import action
from .models import Hotel, Review, Room
from django.conf import settings
from .serializers import HotelSerializer, ReviewSerializer, RoomSerializer
# Create your views here.
RESERVATIONS_SERVICE_URL = settings.RESERVATIONS_SERVICE_URL


def getHeaders(request):
    return {'Authorization': request.headers.get(
        'Authorization')}


class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    # authentication_classes = [UserAuthentication]
    # permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FileUploadParser,)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        queryset = super().get_queryset()
        city = self.request.query_params.get("city")
        if city:
            queryset = queryset.filter(city__icontains=city)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        already_exists = Hotel.objects.filter(
            Q(name=serializer.data['name']) & Q(city=serializer.data['city'])).exists()
        if already_exists:
            return Response({"error": f"El hotel {serializer.data['name']} ya existe en la ciudad de {serializer.data['city']}"}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        Hotel.objects.create(**serializer.validated_data)

    @action(detail=False, methods=["get"])
    def top(self, request):
        headers = getHeaders(request)
        headers["X-Reservation-Gateway-Token"] = settings.RESERVATION_TOKEN
        url = f'{RESERVATIONS_SERVICE_URL}reservations/top_hotels/'
        try:
            response = httpx.get(
                url, timeout=15, headers=headers, params=request.query_params)
            data = response.json()
            room_ids = []

            for item in data:
                if 'room_id' in item:
                    for i in range(item['count']):
                        room_ids.append(item['room_id'])

            if not room_ids:
                return Response([], status=status.HTTP_200_OK)
            room_id_counts = {}
            for room_id in room_ids:
                room_id_counts[room_id] = room_id_counts.get(room_id, 0) + 1
            unique_room_ids = list(room_id_counts.keys())
            rooms = Room.objects.filter(
                id__in=unique_room_ids).select_related('hotel')

            hotel_counts = {}
            for room in rooms:
                # Multiply the room's frequency by the number of times it appeared in the external data
                count = room_id_counts.get(room.id, 0)

                # Accumulate the total count for the hotel
                hotel_id = room.hotel.id
                hotel_counts[hotel_id] = hotel_counts.get(
                    hotel_id, {'hotel': room.hotel, 'count': 0})
                hotel_counts[hotel_id]['count'] += count

            # --- 4. Format the Output ---
            top_hotels_list = []
            for data in hotel_counts.values():
                hotel = data['hotel']
                top_hotels_list.append({
                    "id": hotel.id,
                    "name": hotel.name,
                    "count": data['count']
                })

            # Optional: Sort the list by 'count' descending
            top_hotels_list.sort(key=lambda x: x['count'], reverse=True)
            return Response(top_hotels_list, status=response.status_code)
        except httpx.RequestError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class ReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        hotel_id = self.request.query_params.get("hotel_id")
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        return queryset
    def create(self, request, *args, **kwargs) -> None:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = self.request.user.id
        if user_id is None:
            return Response({"error": "Necesitas estar logeado para realizar una reseña"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(user_id=user_id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        hotel_id = self.request.query_params.get("hotel_id")
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room_number = serializer.data.get("room_number")
        hotel = serializer.data.get("hotel") or None
        check = Room.objects.filter(room_number=room_number, hotel=hotel).exists()
        if check:
            return Response(
                {"error": f"La habitación #{room_number} ya existe en el hotel {hotel}"}, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    def perform_create(self, serializer) -> None:
        Room.objects.create(**serializer.validated_data)
