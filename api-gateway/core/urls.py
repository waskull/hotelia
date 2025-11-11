#from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from gateway.views import (
    AuthLoginView, UserRefreshTokenView,UserView,AuthProfileView,AuthRegisterView,HotelTopView,
    HotelView, ReservationView,ReviewView, RoomView, PaymentView, ChatBotView, GeminiChatBotView, OllamaChatBotView
)

router = DefaultRouter()
router.register(r'auth/login', AuthLoginView, basename="auth")
router.register(r'auth/register', AuthRegisterView, basename="auth-register")
router.register(r'auth/refresh', UserRefreshTokenView, basename="user-refresh-token")
router.register(r'auth', AuthProfileView, basename="user-profile")
router.register(r'users', UserView, basename="users")
router.register(r'hotels', HotelView, basename="hotels")
router.register(r'hotels/top', HotelTopView, basename="hotels-top")
router.register(r'reviews', ReviewView, basename="reviews")
router.register(r'rooms', RoomView, basename="rooms")
router.register(r'reservations', ReservationView, basename="reservation")
router.register(r'payments', PaymentView, basename="payment")
router.register(r'chatbot', ChatBotView, basename="chatbot")
router.register(r'ollama', OllamaChatBotView, basename="chatbot-ollama")
router.register(r'gemini', GeminiChatBotView, basename="chatbot-gemini")

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api_authorization/', include('rest_framework.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'),
         name='swagger-ui'),
]
