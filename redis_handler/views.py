'''
Redis Handler URL Module
File added by Shubhadeep on 27-08-2020
'''

from rest_framework.views import APIView
from rest_framework import parsers
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from redis_handler import pub

class RedisPubDemo(APIView):
    parser_classes = (parsers.JSONParser,)
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        json_data = request.data['data']
        success, msg = pub.publish('demo', json_data)
        return Response({'message': msg, 'success': success}, 
            status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)
        