
from django.urls import path
from llama.views import LlamaBotView

urlpatterns = [
    path('api/llama', LlamaBotView.as_view(),name="llama3.2-chatbot"),
]
