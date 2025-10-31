from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .rag import handle_chat_query
from .serializers import ChatRequestSerializer, ChatResponseSerializer


class LlamaBotView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query = serializer.validated_data.get("query")
        user_id = serializer.validated_data.get("user_id", "anon")
        try:
            answer = handle_chat_query(query, user_id)

            response_data = {
                "user_id": user_id,
                "query": query,
                "response": answer,
            }

            response_serializer = ChatResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response(
                {"error": f"Ocurrió un error al procesar la solicitud: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
