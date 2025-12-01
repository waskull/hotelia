from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reservations.views import ReservationViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r'reservations', ReservationViewSet, basename="reservation")
router.register(r'payments', PaymentViewSet, basename="payment")


urlpatterns = [
    path('api/', include(router.urls)),
]
