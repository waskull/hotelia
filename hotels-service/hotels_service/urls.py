#from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from hotels.views import HotelViewSet, RoomViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r'hotels', HotelViewSet, basename="hotel")
router.register(r"reviews",ReviewViewSet, basename="review")
router.register(r'rooms', RoomViewSet, basename="room")

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
urlpatterns += static(settings.STATIC_URL, 
   document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, 
   document_root=settings.MEDIA_ROOT
)