from rest_framework.authentication import BaseAuthentication
from drf_spectacular.extensions import OpenApiAuthenticationExtension

class ExternalServiceAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return None 

class BearerAuthExternalServiceScheme(OpenApiAuthenticationExtension):
    target_class = 'gateway.auth_schemes.ExternalServiceAuthentication'
    name = 'ExternalBearerAuth' 
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT' 
        }