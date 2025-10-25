from django.conf import settings
from django.http import JsonResponse
from rest_framework import status

class HotelGatewayMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.valid_token = settings.HOTELS_GATEWAY_TOKEN

    def __call__(self, request):
        gateway_hotel_token = request.headers.get('X-Hotel-Gateway-Token')
        if request.path.startswith('/api/'):
            if gateway_hotel_token != self.valid_token:
                return JsonResponse({'error': 'No tienes permiso para realizar dicha accion'}, status=status.HTTP_401_UNAUTHORIZED)
        
        response = self.get_response(request)
        return response