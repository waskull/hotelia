
from django.urls import path
from llama.views import OLlamaBotView, ChatLlamaCppView, ChatGeminiView

urlpatterns = [
    path('api/ollama/', OLlamaBotView.as_view(),name="ollama-chatbot"),
    path("api/llamacpp/", ChatLlamaCppView.as_view(), name="llamacpp-chatbot"),
    path("api/gemini/", ChatGeminiView.as_view(), name="gemini-chatbot")
]
