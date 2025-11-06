
from django.urls import path
from llama.views import LlamaBotView, ChatLlamaCppView, UserHistoryView

urlpatterns = [
    path('api/llama', LlamaBotView.as_view(),name="llama3.2-chatbot"),
    path("api/history/<str:user_id>/", UserHistoryView.as_view(), name="chat-history"),
    path("api/llamacpp/", ChatLlamaCppView.as_view(), name="llamacpp-chatbot"),
]
