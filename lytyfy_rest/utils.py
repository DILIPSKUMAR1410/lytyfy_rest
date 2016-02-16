from rest_framework.response import Response
from rest_framework import status
from lytyfy_rest.models import Token

def token_required(func):
    def inner(self,request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)
        if auth_header is not None:
            tokens = auth_header.split(' ')
            if len(tokens) == 2 and tokens[0] == 'Token':
                token = tokens[1]
                try:
                    request.token = Token.objects.get(token=token)
                    return func(self,request)
                except Token.DoesNotExist:
                    return Response({'error': 'Token not found'},status=status.HTTP_401_UNAUTHORIZED)
        return Response({'error': 'Invalid Header'},status=status.HTTP_401_UNAUTHORIZED)
    return inner