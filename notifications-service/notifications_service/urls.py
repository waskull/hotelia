from django.contrib import admin
from django.urls import path
from notifications.views import SendEmailView

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('api/email/', SendEmailView.as_view(), name='email-service'),
]