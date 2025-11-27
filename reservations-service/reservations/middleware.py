from django.conf import settings
from django.http import JsonResponse
from rest_framework import status

class NotificationGatewayMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.valid_token = settings.RESERVATIONS_GATEWAY_TOKEN

    def __call__(self, request):
        gateway_notification_token = request.headers.get('X-Reservation-Gateway-Token')
        if request.path.startswith('/api/'):
            if gateway_notification_token != self.valid_token:
                return JsonResponse({'error': 'No tienes permiso para realizar dicha accion'}, status=status.HTTP_401_UNAUTHORIZED)
        
        response = self.get_response(request)
        return response