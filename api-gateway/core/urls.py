"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from gateway.views import (
    AuthView, UserRefreshTokenView,UserView,
    HotelView, ReservationView,ReviewView, RoomView, PaymentView, ChatBotView
)

router = DefaultRouter()
router.register(r'auth', AuthView, basename="auth")
router.register(r'auth/refresh', UserRefreshTokenView, basename="user-refresh-token")
router.register(r'users', UserView, basename="users")
router.register(r'hotels', HotelView, basename="hotels")
router.register(r'reviews', ReviewView, basename="reviews")
router.register(r'rooms', RoomView, basename="rooms")
router.register(r'reservations', ReservationView, basename="reservation")
router.register(r'payments', PaymentView, basename="payment")
router.register(r'chatbot', ChatBotView, basename="chatbot")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api_authorization/', include('rest_framework.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'),
         name='swagger-ui'),
]
