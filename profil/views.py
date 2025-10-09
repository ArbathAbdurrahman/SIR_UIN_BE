from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import *

from .serializers import *

class ProfileAPIView(APIView):
    def get(self, request):
        profil = get_object_or_404(UserProfile, user = request.user)
        serializer = ProfileSerializers(profil)
        return Response(serializer.data, status=HTTP_200_OK)
    
    def patch(self, request):
        profil = get_object_or_404(UserProfile, user = request.user)
        serializer = ProfileSerializers(profil, data= request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)