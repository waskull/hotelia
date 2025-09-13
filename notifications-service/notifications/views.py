from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from .serializers import EmailSerializer

class SendEmailView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            try:
                subject = serializer.validated_data['subject']
                body = serializer.validated_data['body']
                destinations = serializer.validated_data['destinations']
                
                send_mail(subject, body, None, destinations)
                
                return Response({'mensaje': 'Correo enviado con éxito.'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)