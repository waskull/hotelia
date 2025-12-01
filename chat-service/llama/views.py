from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .authentication import UserAuthentication
from .rag import handle_chat_query, get_user_history, search_user_history
from .serializers import ChatRequestSerializer, ChatResponseSerializer, UserHistoryResponseSerializer
from .rag_llamacpp import handle_chat_query_llamacpp, get_user_history as get_user_history_llamacpp, search_user_history as search_user_history_llamacpp
from .rag_gemini import handle_chat_query_gemini, gemini_get_user_history, search_user_history_gemini

class OLlamaBotView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query = serializer.validated_data.get("query")
        user_id = str(request.user.id) if request.user.is_authenticated else "anon"
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
        
    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        search = request.query_params.get("search")
        user_id = str(request.user.id) if request.user.is_authenticated else "anon"
        try:
            if search:
                history = search_user_history(user_id, search=search, n_results=limit)
            else:
                history = get_user_history(user_id=user_id, limit=limit)
            response_serializer = UserHistoryResponseSerializer({
                "user_id": user_id,
                "history": history
            })
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"No se pudo obtener el historial: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatLlamaCppView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query = serializer.validated_data.get("query")
        user_id = str(request.user.id) if request.user.is_authenticated else "anon"

        try:
            answer = handle_chat_query_llamacpp(query, user_id)
            response_data = {"user_id": user_id,
                             "query": query, "response": answer}
            response_serializer = ChatResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        search = request.query_params.get("search")
        user_id = str(request.user.id) if request.user.is_authenticated else "anon"
        try:
            if search:
                history = search_user_history_llamacpp(user_id, search=search, n_results=limit)
            else:
                history = get_user_history_llamacpp(user_id=user_id, limit=limit)
            response_serializer = UserHistoryResponseSerializer({
                "user_id": user_id,
                "history": history
            })
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"No se pudo obtener el historial: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ChatGeminiView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query = serializer.validated_data.get("query")
        user_id = str(request.user.id) if request.user.is_authenticated else "anonimo"
        try:
            answer = handle_chat_query_gemini(query, user_id)
            response_data = {"user_id": user_id,
                             "query": query, "response": answer}
            response_serializer = ChatResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        search = request.query_params.get("search")
        user_id = str(request.user.id) if request.user.is_authenticated else "anonimo"
        try:
            if search:
                history = search_user_history_gemini(user_id, search=search, n_results=limit)
            else:
                history = gemini_get_user_history(user_id=user_id, limit=limit)
            response_serializer = UserHistoryResponseSerializer({
                "user_id": user_id,
                "history": history
            })
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"No se pudo obtener el historial: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )