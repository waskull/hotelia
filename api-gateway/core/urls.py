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
#from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from gateway.views import (
    UserLoginView, UserRegisterView, UserDetailView,UserProfileView,
    HotelListView, HotelDetailView,
    ReservationListView, ReservationDetailView,
    CreateReservationView, RoomListView, RoomDetailView
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/register/', UserRegisterView.as_view(), name='user-register'),
    path('auth/login/', UserLoginView.as_view(), name='user-login'),
    path('auth/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),

    # Rutas para el servicio de hoteles
    path('hotels/', HotelListView.as_view(), name='hotel-list'),
    path('hotels/<int:pk>/', HotelDetailView.as_view(), name='hotel-detail'),

    # Rutas para el servicio de habitaciones
    path('rooms/', RoomListView.as_view(), name='room-list'),
    path('rooms/<int:pk>/', RoomDetailView.as_view(), name='room-detail'),

    # Rutas para el servicio de reservaciones
    path('reservations/', ReservationListView.as_view(), name='reservation-list'),
    path('reservations/create/', CreateReservationView.as_view(), name='reservation-create'),
    path('reservations/<int:pk>/', ReservationDetailView.as_view(), name='reservation-detail'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
