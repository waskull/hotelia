from rest_framework import serializers

class ChatRequestSerializer(serializers.Serializer):
    query = serializers.CharField(
        required=True,
        help_text="Texto o pregunta del usuario para el asistente de reservas."
    )
    user_id = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Identificador opcional del usuario. Se usa para mantener el historial contextual en ChromaDB."
    )

class ChatResponseSerializer(serializers.Serializer):
    user_id = serializers.CharField(help_text="ID del usuario que hizo la consulta.")
    query = serializers.CharField(help_text="Pregunta original enviada por el usuario.")
    response = serializers.CharField(help_text="Respuesta generada por el modelo LLaMA u Ollama.")
